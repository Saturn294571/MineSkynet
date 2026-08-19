# MineSkynet Odyssey MVP 환경·의존성 진단 보고서

작성일: 2026-08-19  
진단 대상: `experiment/modern-odyssey` (`80a42fc`)  
목적: 모델 학습과 다중 에이전트 구현에 앞서, **Odyssey 기반 Minecraft 실험을 신뢰성 있게 반복 실행하기 위한 최소 부품과 의존성**을 확정한다.

## 1. 결론

현재 최우선 과제는 LoRA나 모델 비교가 아니라 **Minecraft 서버 → Mineflayer executor → skill 실행 → 상태 기반 성공 판정**의 단일 실행 경로를 안정화하는 것이다.

현재 `Odyssey` 클래스는 raw skill만 실행해도 Planner, Critic, SkillManager, Chroma, sentence-transformer와 여러 LLM 관련 모듈을 한꺼번에 초기화한다. Node bridge도 나무 채굴만 수행할 때조차 PVP와 Hawkeye를 포함한 모든 plugin을 무조건 로드한다. 따라서 지금의 `requirements.txt`는 실제 기능상 최소 의존성이 아니라 **코드 결합 때문에 강제로 설치되는 의존성 집합**이다.

MineSkynet의 첫 실행 gate는 다음 한 사이클로 제한한다.

```text
고정된 단일 subgoal + 제한된 candidate skill ID
    → actor endpoint가 skill ID 하나를 선택
    → whitelist 기반 skill registry가 기존 JavaScript skill 실행
    → Mineflayer가 Minecraft에 행동 적용
    → inventory/world-state delta로 성공 판정
    → 구조화 로그 저장
```

여기서 반드시 구분할 것은 **gate의 최소 설치 profile에서 비활성화하는 것**과 **연구 시스템에서 제거하는 것**이다. E0와 E1은 Minecraft 행동 계층과 API 계약을 모델 품질로부터 분리하기 위한 통제 실험이므로 다음 기능을 기본 profile에서 로드하지 않는다.

- 자동 장기 계획과 task decomposition
- LLM critic, comment agent, reflection
- Chroma와 Sentence Transformer 기반 skill retrieval
- 장기 memory, 새 skill 생성, actor의 in-context adaptation
- LoRA 학습과 MineMA 학습 데이터셋
- PVP, Hawkeye, 전투 benchmark plugin
- VillagerAgent/Multi-Agent orchestration
- Tailscale과 세 edge node 분산 실행

이는 영구 제거 목록이 아니다. 논문의 Odyssey를 재현하거나 Odyssey 대비 성능을 주장하려면 다음 기능을 별도 baseline profile에서 보존해야 한다.

- 40개 primitive skill과 183개 compositional skill로 구성된 open-world skill library
- 자연어 subgoal과 skill description을 vector로 변환하는 semantic encoder
- vector similarity 기반 top-5 candidate skill retrieval
- planner–actor–critic과 실행 feedback
- 비교 대상인 MineMA와 공식 benchmark별 실행 plugin

여기에 Voyager 계열의 **능동적 skill 학습**은 별도 생명주기로 보존한다. Voyager는 automatic curriculum이 과제를 제안하고, actor가 JavaScript 프로그램을 생성한 뒤 환경 feedback·execution error·self-verification을 이용해 반복 수정하며, 성공한 프로그램만 description과 embedding을 붙여 versioned skill library에 저장하고 이후 과제에서 다시 검색한다. 이 경로는 E0~E3의 단계별 MVP에서는 비활성화하지만 `voyager-lifelong` baseline과 이를 Odyssey 구성에 결합한 실험용 `odyssey-full` profile에서는 유지한다.

다만 공개 Odyssey 논문 baseline과 Voyager의 lifelong 기능을 같은 것으로 기술하지 않는다. 공개 Odyssey는 미리 구축한 40+183 skill과 recursive prerequisite 실행을 중심으로 하며, 현재 저장소에도 `SkillManager.add_new_skill()`은 남아 있지만 main learning loop의 호출은 주석 처리돼 있다. 따라서 `odyssey-legacy`는 논문 재현용 고정 library baseline이고, `odyssey-full`은 능동적 생성·수정·축적을 복원한 확장 profile이다.

논문은 자연어 subgoal을 Sentence Transformer로 encoding하고 skill description과 유사도를 계산해 top-5를 actor에게 제공한다. 또한 skill library 제거 ablation에서 성능 저하를 보고한다. 다만 이 ablation은 Sentence Transformer만 단독 제거한 실험이 아니므로, **semantic retrieval 기능은 보존하되 특정 `sentence-transformers` 패키지와 Chroma 구현체는 통제 실험을 통해 교체할 수 있다**고 해석한다.

첫 두 gate의 범위는 **원본 Odyssey 전체 재현**이 아니라 **Odyssey-derived actor/executor MVP**다. strict `skill_id` registry도 원본의 JavaScript code 선택·분석 경로를 단순화한 MineSkynet 계약이다. 원본 Odyssey 성능을 재현했다고 주장하려면 이후 full skill library, Sentence Transformer top-5 retrieval, planner, actor, critic과 공식 benchmark 조건을 `odyssey-legacy` profile에서 다시 켜야 한다.

## 2. 교수님 피드백을 구현 결정으로 변환

| 피드백 | 이번 결정 |
|---|---|
| 환경 설정이 최우선 | raw 제작대까지 반복 통과하기 전에는 LoRA·INT4·다중 노드 구현을 중단한다. |
| 제안 기능에 필요한 최소 의존성만 유지 | Odyssey monolith를 실행환경, controller, model service 경계로 분리하고 optional dependency의 eager import를 제거한다. |
| Gemma 3 1B 성능이 아쉽고 약 4B급 최신 모델 필요 | MVP API를 모델 비종속적으로 만들고, 환경 통과 후 4B급 instruct 모델을 **파인튜닝 없이 먼저** 연결한다. 1B는 저사양 ablation 후보로만 남긴다. |
| MoE 모델의 파인튜닝 가능성 | 모델 구조와 학습법은 환경 의존성이 아니다. 후보 모델의 실제 구조를 모델 카드로 확인한 뒤 별도 feasibility 실험으로 다루며 MVP를 막지 않는다. |
| LoRA의 의미가 약하면 과감히 중단 | base/quantized model이 online atomic task를 수행한 뒤에만 LoRA를 평가한다. 고정 actor 평가셋과 Minecraft 성공률 개선이 없으면 중단한다. |
| 새 기억을 덧씌우면 기존 능력을 잃을 수 있음 | edge actor는 stateless skill selector로 고정한다. memory와 실패 이력은 추후 cloud planner/state manager에만 둔다. |
| 복잡한 문제를 더 복잡하게 만들지 말 것 | E0/E1 실행 profile에서는 retrieval, reflection, multi-agent, networking을 비활성화하고 한 bot·한 world·두 atomic task만 검증한다. 기능 삭제 판단은 후속 profile의 비교 실험으로 분리한다. |

## 3. 현재 확인된 환경 상태

### 3.1 통과한 부분

- Docker Minecraft 서버는 현재 `healthy` 상태다.
- Minecraft 1.19.4, Java 17, Fabric Loader 0.15.11 조합으로 서버가 기동된다.
- Node.js 20.13.1에서 Mineflayer bot 접속과 observation 반환이 확인됐다.
- raw `mineWoodLog` smoke test가 실제 `oak_log` 인벤토리 증가까지 통과했다.
- Odyssey Python 환경과 LLM Backend 환경 모두 `pip check`를 통과한다.
- Odyssey 주요 모듈 import가 성공한다. 다만 LangChain legacy import deprecation warning이 발생한다.
- MineMA Backend의 별도 환경과 endpoint 단일 추론은 이전 단계에서 확인됐다.

### 3.2 아직 통과하지 못한 부분

- raw `craftCraftingTable`은 Mineflayer 4.8.1의 `window_click` packet 직렬화 과정에서 빈 slot이 `undefined`로 전달되어 실패한다.
- 따라서 “나무 채굴 → 판자 제작 → 작업대 제작” 실행 계층은 아직 안정화되지 않았다.
- MineMA가 candidate skill을 선택하고 실제 Minecraft 행동까지 완료하는 model-in-the-loop 검증은 아직 끝나지 않았다.
- `npm ls --depth=0`은 로컬 `mineflayer-collectblock@1.4.1`을 `invalid`로 판정한다. 현재 설치 디렉터리가 우연히 실행되더라도 clean install 재현성은 통과한 상태가 아니다.
- Python의 `javascript.require()`가 요구하는 `@babel/core`, `@babel/generator`는 Node `package.json`에 선언되어 있지 않고 현재 local npm tree에도 없다. 별도 smoke script는 Babel 경로를 우회하므로 raw smoke 성공이 `Odyssey.run_raw_skill()` 성공을 뜻하지 않는다.

### 3.3 현재 버전 snapshot

| 계층 | 현재 상태 |
|---|---|
| OS-side Python | Conda Python 3.10.20 |
| Odyssey | LangChain 0.2.17, Chroma 0.3.29, sentence-transformers 5.6.0, Transformers 5.14.1, Torch 2.13.0 |
| LLM Backend | Python 3.10.20, Torch 2.2.0, Transformers 4.43.3, FastAPI 0.112.2 |
| Node | 20.13.1, npm 10.5.2 |
| Mineflayer | 4.8.1 |
| Minecraft server | 1.19.4 / Fabric 0.15.11 / Java 17 |
| Docker | Engine 29.1.3, Compose 2.40.3 |

`pip check` 성공은 패키지 metadata 요구사항이 맞는다는 뜻일 뿐, Odyssey 전체 실행 호환성을 보장하지 않는다. 특히 Odyssey `requirements.txt`는 Chroma 외 대부분을 pin하지 않아 같은 설치 명령이 이후 다른 환경을 만들 수 있다.

### 3.4 Gate E0 작업 tree 진행 상황: 2026-08-20

진단 뒤 E0 전용 Node profile을 분리하는 작업을 시작했다. 아래 결과는 아직 commit/tag로 고정된 E0 합격 상태가 아니라 현재 작업 tree의 중간 검증 결과다.

- bridge package를 `mineskynet-mineflayer-bridge@0.1.0`으로 구분하고 Node 20.13.1/npm 10.5.2를 명시했다.
- E0에 필요 없는 PVP, Hawkeye, viewer와 미사용 direct dependency를 기본 Node profile에서 제거했다. combat profile 복원 여부는 별도 검증한다.
- `package-lock.json`을 Git 추적 대상으로 전환했다.
- Mineflayer 4.25.0, minecraft-data 3.83.0과 동시대 Prismarine 묶음을 E0 candidate로 고정했다.
- `npm ci`, local collectblock TypeScript build, `node --check`, `npm ls --depth=0`은 exit code 0을 반환했다.
- `/health`와 `/version` 응답을 추가하고 bot 미접속 상태의 응답을 확인했다.
- 현재 Docker image digest는 `sha256:5b3e96bcd7dace8ab7be89c245dc9ba0b1573fdef2f01d3e101ac40e7843fa70`, 기존 world seed는 `7634567288700934061`로 확인했다.
- bot 30초 finite position과 raw 나무·작업대 hard-reset 회귀를 각각 10/10 통과했다.
- request-local bot lifecycle, `/step` exception listener 정리, 실패 후 복구 회귀를 통과했다.
- offline-mode bot UUID를 repository `OPS_FILE`로 고정해 완전히 새 mod-free server의 첫 hard reset과 대표 행동을 통과했다.
- 자동 runner가 실행별 raw JSON·wall-clock latency·환경·Minecraft log를 저장하며 최종 실행은 총 20/20이었다. commit/tag 고정 전까지 작업 tree candidate로 취급한다.

## 4. 코드상 의존성이 부풀려지는 원인

### 4.1 Python monolith

[`odyssey.py`](../../Odyssey/odyssey/odyssey.py)는 `Odyssey()` 생성 시 다음 객체를 항상 만든다.

1. `VoyagerEnv`
2. `ActionAgent`
3. `PlannerAgent`
4. `CriticAgent`
5. `CommentAgent`
6. `SkillManager`
7. `EventRecorder`

이 때문에 raw skill이나 fixed subgoal만 실행해도 Planner와 SkillManager가 각각 HuggingFace embedding model과 Chroma DB를 초기화한다. E0/E1에는 필요 없고 후속 retrieval profile에만 필요한 `langchain`, `langchain-community`, `chromadb`, `sentence-transformers`가 모든 실행환경의 필수품처럼 바뀐다.

반대로 능동 skill 경로는 dependency가 설치됐다는 이유만으로 작동한다고 볼 수 없다. `SkillManager.add_new_skill()`은 code·description·JSON·Chroma index를 갱신하는 구현을 갖고 있지만 `Odyssey.learn()`의 성공 후 호출은 주석 처리돼 있고, description 생성이 참조하는 `self.llm`도 `SkillManager`에서 초기화되지 않는다. E4에서는 package 설치 여부가 아니라 이 전체 write lifecycle을 별도 contract test로 복구해야 한다.

또한 [`bridge.py`](../../Odyssey/odyssey/env/bridge.py)는 Docker의 외부 Minecraft 서버를 사용할 때도 [`minecraft_launcher.py`](../../Odyssey/odyssey/env/minecraft_launcher.py)를 import하므로 `minecraft-launcher-lib`가 강제로 필요하다. `gymnasium`은 `VoyagerEnv`가 `gym.Env`를 상속하기 위해서만 사용된다.

### 4.2 Node plugin 일괄 로드

[`index.js`](../../Odyssey/odyssey/env/mineflayer/index.js)는 bot spawn마다 다음 plugin을 모두 로드한다.

- `mineflayer-pathfinder`
- `mineflayer-tool`
- local patched `mineflayer-collectblock`

E0 기본 profile은 앞의 세 개만 로드하도록 정리했다. PVP와 Hawkeye는 repository에서 삭제하지 않고 combat profile에서만 복원한다.

### 4.3 범용 실행 경로가 아닌 hard-coded benchmark 경로

- `inference_sub_goal()`도 매 subgoal마다 Planner의 Minecraft QA endpoint와 embedding cache를 호출한다.
- `inference()`는 일반 task 종료 후 combat setup, monster reranking, summon, kill, comment agent를 hard-coded로 실행한다.
- `CriticAgent.check_subgoal_success()`는 제작대와 pickaxe, diamond 몇 개만 검사하고 나무 subgoal에는 결과를 반환하지 않는다.
- `ActionAgent`는 존재하지 않는 skill 이름이 나오면 오류로 중단하지 않고 candidate 첫 항목으로 조용히 fallback한다.
- `ActionAgent.render_human_message()`는 observation 필드를 읽지만 실제 prompt에는 task, programs, critique 중심으로만 넣는다.

따라서 현재 진입점을 그대로 최소 환경의 기준으로 삼으면 환경 문제와 연구 logic 문제가 섞인다.

## 5. 의존성 분류

### 5.1 Minecraft server 계층

| 항목 | 현재 코드 | profile 판단 | 이유 |
|---|---|---|---|
| Docker Engine/Compose | 사용 | 유지 | 서버를 host 환경과 격리하고 재현하기 가장 쉽다. |
| Minecraft server | 1.19.4 | 우선 유지 | Node 계층 문제를 해결하는 동안 game version까지 동시에 바꾸지 않는다. |
| Java 17 | 사용 | 현재 profile 유지 | 현 서버 조합에서 검증된 runtime이다. host Java 대신 container에만 둔다. |
| Fabric API | 기존 modded fixture에서 사용 | E0/mineskynet-core 기본 profile에서는 제외 가능 | 외부 mod JAR가 전혀 없는 Fabric server에서 E0 raw 행동이 통과했다. combat 등 후속 mod가 요구할 때만 profile별로 복원한다. |
| Multiplayer Server Pause | legacy `bridge.py`가 `/pause` 호출 | `mineskynet-core`에서는 제거 | LLM 추론 중 world를 멈추면 연구 대상인 latency/makespan을 숨긴다. E0 direct bridge 경로는 호출하지 않으며 mod-free 시험도 통과했다. |
| iChunUtil | Server Pause 계열 dependency | pause와 함께 E0 기본 profile에서 제외 | MineSkynet 핵심 기능이 아니며 mod-free E0 통과로 불필요함을 확인했다. |
| CompleteConfig | Odyssey 설치 문서상 Server Pause 계열 dependency | pause와 함께 E0 기본 profile에서 제외 | dependency edge를 개별 분리하지는 않았지만 전체 pause bundle 제거 상태에서 E0가 통과했다. 독립적으로 필요한 후속 mod가 생길 때만 복원한다. |

가장 짧은 복구 경로에서는 현재 1.19.4/Fabric 서버를 그대로 유지한다. executor가 통과한 뒤 `/pause` 의존성을 제거하고, mod 없는 서버 또는 최소 Fabric server profile을 별도로 검증한다.

현재 Compose image `itzg/minecraft-server:java17`은 mutable tag다. 최종 재현 profile에서는 image digest까지 고정해야 한다.

### 5.2 Node/Mineflayer executor 계층

#### 나무·제작대 MVP에 필요한 runtime

- `express`: `/start`, `/step`, `/stop`, `/health` API
- `mineflayer`: Minecraft bot core
- `mineflayer-pathfinder`: 탐색과 제작대 접근
- `mineflayer-tool`: 채굴 도구 선택
- `mineflayer-collectblock`: 블록 채굴과 drop 회수
- `minecraft-data`: block, item, recipe lookup
- `vec3`: 탐색 방향과 좌표

`mineflayer-collectblock` 자체가 Mineflayer, pathfinder, tool에 의존하므로 이 네 패키지는 하나의 호환 묶음으로 pin하고 시험해야 한다.

#### E0/E1 기본 profile에서 제외할 runtime

- `mineflayer-pvp`, `minecrafthawkeye`: combat benchmark profile에서만 복원한다.
- `prismarine-viewer`: 시각 디버깅 profile에서만 사용하며 headless benchmark에는 포함하지 않는다.

#### build/dev로 이동할 항목

- `typescript`: local collectblock build용
- `mocha`: test용
- `prettier`: formatting용

`prismarine-*`의 다수 패키지는 Mineflayer의 transitive dependency다. 현재 직접 pin은 legacy 호환을 위해 생겼을 가능성이 있으므로 곧바로 삭제하지 않고, clean lockfile에서 `npm ls`와 atomic test를 통과한 뒤 중복 direct dependency를 제거한다.

`body-parser`는 Express의 built-in JSON parser로 대체 가능하며 `magic-string`, `graceful-fs`도 실제 direct 사용 여부를 확인한 뒤 제거 후보로 둔다.

### 5.3 Python controller 계층

#### 현재 코드 그대로 실행할 때 강제로 필요한 묶음

- `requests`, `psutil`, `coloredlogs`
- `gymnasium`
- `minecraft-launcher-lib`
- `javascript`
- `langchain`, `langchain-community`
- `chromadb==0.3.29`
- `sentence-transformers`
- `dashscope`

이 목록은 “기능상 최소”가 아니다. eager import와 일괄 초기화 때문에 필요한 목록이다.

#### 구조 분리 후 actor/executor MVP에 필요한 묶음

- Python 3.10
- `requests`: Node bridge와 model endpoint 호출
- `psutil`: Python controller가 Node subprocess를 직접 관리할 때만 유지
- `coloredlogs`: 선택 사항; 표준 `logging`으로 대체 가능

Node bridge를 별도 service로 실행하면 controller는 `requests` 외 third-party runtime이 없어도 구현 가능하다. smoke test 두 개는 현재도 Python 표준 라이브러리 `urllib`만 사용한다.

#### 기능 보존 여부와 package 배치

| 기능·패키지 | E0/E1 | Odyssey baseline 또는 후속 profile | 판단 |
|---|---|---|---|
| semantic skill retrieval | 비활성화 | `odyssey-retrieval`, `odyssey-legacy`, `voyager-lifelong`, `odyssey-full`, 필요 시 `mineskynet-core`에서 활성화 | 논문의 핵심 actor 경로이자 동적 skill 재사용 경로이므로 기능을 보존한다. |
| `sentence-transformers` | 설치하지 않음 | original checkpoint를 쓰는 retrieval extra로 설치 | 특정 패키지는 구현체지만 자연어 query/skill description encoder는 보존한다. |
| `chromadb` | 설치하지 않음 | legacy/full의 기본 vector store로 우선 유지; parity test 뒤 대체 구현 비교 가능 | 정적 223개 검색뿐 아니라 새 skill의 동적 add/delete/persist에도 사용된다. 신뢰받는 외부 구현을 임의로 재작성하지 않는다. |
| full skill library | 두 atomic skill만 등록 | 40 primitive + 183 compositional skill 복원 | 원본 Odyssey 비교와 retrieval 평가에 필수다. |
| planner·critic·reflection | 초기화하지 않음 | `odyssey-legacy`와 기능별 E3 ablation에서 복원 | 논문 architecture와 planner/skill-library ablation을 보존해야 한다. |
| automatic curriculum | 비활성화 | `voyager-lifelong`, `odyssey-full`에서 활성화 | 현재 능력과 성공·실패 이력에 따라 다음 학습 과제를 제안하는 Voyager 핵심 기능이다. |
| iterative code generation·repair | 비활성화 | `voyager-lifelong`, `odyssey-full`의 격리된 strong-model worker에서 활성화 | 환경 feedback·execution error·critique를 이용한 프로그램 개선을 보존한다. |
| self-verification과 skill commit | deterministic verifier만 사용 | Full profile에서 LLM verification과 deterministic check를 함께 사용 | 검증에 성공한 프로그램만 versioned 저장·색인해야 library 오염을 막는다. |
| persistent skill lifecycle | 쓰기 금지 registry | Full profile에서 code·description·embedding·provenance·version을 원자적으로 저장 | 생성, 수정, rollback, 재색인과 이후 재사용이 함께 보존돼야 한다. |
| `langchain`, `langchain-community` | 설치하지 않음 | Odyssey 공개 코드와 Full lifecycle adapter에서 우선 유지 | 검증된 외부 추상화를 기본으로 사용하며, 명확한 장애나 측정된 이득이 있을 때만 contract test를 통과한 대체 구현을 채택한다. |
| `gymnasium` | 제거 | 표준 Env API가 필요한 별도 학습 profile에서만 복원 | 현재 online controller는 plain class로 충분하다. |
| `minecraft-launcher-lib` | 제거 | local Minecraft client launcher profile에서만 복원 | Docker 외부 서버를 쓰는 E0에는 불필요하다. |
| `javascript` 및 Babel | strict skill-ID 경로에서는 제거 | 원본 JavaScript code 선택·AST parsing과 Full code generation/repair profile에서는 유지 | registry 계약은 MineSkynet 단순화이며 동적 code-as-action 경로를 대체하지 않는다. |
| `dashscope`, `openai` | controller core에서 제거 | 선택한 model provider adapter 환경에만 설치 | 특정 SDK는 교체 가능하지만 curriculum·code generation·repair·description 생성 역할의 강한 모델 endpoint는 Full profile에 필요하다. |
| `tqdm`, `chardet`, `cchardet`, `tiktoken` | 제거 | 직접 사용이 확인되는 도구 profile에서만 복원 | 현재 Odyssey runtime의 직접 사용 근거가 없다. |
| 중복 `setuptools` | 제거 | build dependency로 한 번만 선언 | 기능 변화가 없다. |

이 분류에서 `제거`는 모든 연구 profile과 repository에서 삭제한다는 뜻이 아니다. core environment에서 분리하고, 해당 기능을 평가하는 profile의 lockfile 또는 optional extra로 이동한다는 뜻이다.

### 5.4 Model service 계층

MVP가 요구하는 것은 특정 모델이나 기존 `LLM-Backend` 전체가 아니라 다음 계약뿐이다.

```http
POST /v1/actor/select
Content-Type: application/json
```

```json
{
  "request_id": "...",
  "subgoal": "mine one wood log",
  "observation": {"inventory": {}, "nearby_blocks": ["oak_log"]},
  "candidate_skills": ["mineWoodLog", "craftCraftingTable"]
}
```

```json
{
  "skill_id": "mineWoodLog"
}
```

반환값은 candidate 안의 exact ID여야 하며 자유 형식 JavaScript 생성을 허용하지 않는다. timeout, non-2xx, malformed JSON, unknown skill은 명시적 실패로 기록하고 조용한 fallback을 금지한다.

기존 [`LLM-Backend`](../../LLM-Backend)는 `POST /{model_name}`에 `system_prompt`, `user_prompt`를 받고 `data` 문자열을 반환한다. 이 backend는 다음 이유로 core가 아니라 legacy adapter로 분류한다.

- Llama2/Llama3 이름 prefix에 따라 loader가 hard-coded돼 있다.
- Llama3는 BF16 load만 지원하고 Gemma 계열 공통 loader가 없다.
- local Transformers, BitsAndBytes, API provider가 한 환경에 섞여 있다.
- controller 쪽 호출에는 timeout, status 검사, response schema 검증이 없다.

환경 검증은 먼저 deterministic stub actor로 수행하고, 그 다음 파인튜닝하지 않은 4B급 instruct model을 fixed-candidate 조건에 연결한다. 이후 semantic retrieval을 켜 candidate 생성과 actor 선택 오류를 분리한다. 모델 service는 별도 Conda/container 환경으로 유지해 Minecraft runtime과 PyTorch/Transformers 충돌을 차단한다.

### 5.5 E0/E1 기본 설치에서 제외할 repository 영역

- `MineMA-Model-Fine-Tuning`: 학습 실험 전용
- `research/mineskynet_finetuning`: offline 연구 기록 전용
- `MC-Crawler`: 데이터 생성 전용
- `Multi-Agent`: 최종 orchestration 단계 또는 비교 baseline 전용
- 전체 `MC-Comprehensive-Skill-Library`: E0/E1에는 필요한 skill 몇 개만 registry에 등록하고 `odyssey-retrieval`부터 전체 library를 복원

파일을 삭제하거나 연구 범위에서 영구 제거한다는 뜻은 아니다. 해당 gate의 설치 및 실행 profile에서 제외한다는 뜻이다.

## 6. 최소 실행 구조

```text
┌──────────────────────────────────────────────────────┐
│ 3090 host                                            │
│                                                      │
│  Docker Minecraft server                             │
│          ▲                                           │
│          │ Minecraft protocol                        │
│  Node Mineflayer executor :3000                      │
│          ▲                                           │
│          │ strict action API                         │
│  Minimal Python controller                           │
│          │                                           │
│          └──── actor API ────> stub → real 4B model  │
└──────────────────────────────────────────────────────┘
```

첫 환경에서는 모든 서비스가 3090 host 한 대에 존재한다. Tailscale, Raspberry Pi, GTX 1050 Ti는 환경 자체가 아니라 이후 배포·routing 실험의 변수다. Raspberry Pi가 Minecraft server까지 실행할 필요는 없다.

서비스별 환경은 다음처럼 분리한다.

```text
Minecraft server  : Docker image + compose lock/profile
Mineflayer        : Node project + exact package-lock
Controller        : minimal Python environment
Model service     : 별도 Python/CUDA environment 또는 외부 API adapter
Fine-tuning       : 별도 training environment, MVP runtime에 미포함
```

기능과 dependency는 다음 실행 profile로 분리한다.

| profile | 목적 | 활성 기능 |
|---|---|---|
| `e0-executor` | Minecraft 행동 계층 검증 | 서버, Mineflayer, 두 raw skill, state verifier |
| `e1-stub` | controller 계약 검증 | strict registry, fixed candidate, deterministic actor |
| `e2-actor-fixed` | 모델 자체의 skill 선택 검증 | 실제 actor model, fixed candidate, strict output validation |
| `odyssey-retrieval` | 논문의 semantic retrieval 재현 | full skill description, Sentence Transformer, top-5 similarity retrieval |
| `odyssey-legacy` | 원본 Odyssey baseline | full skill library, retrieval, planner, actor, critic, MineMA |
| `voyager-lifelong` | 전신 연구의 lifelong baseline | automatic curriculum, iterative code generation/repair, self-verification, dynamic skill commit·retrieval |
| `odyssey-full` | Odyssey 구성에 능동 skill lifecycle을 복원한 확장 실험 | Odyssey 223-skill baseline + versioned skill 생성·수정·축적·재사용 |
| `mineskynet-core` | 제안 시스템 | cloud/controller retrieval·candidate filtering, stateless edge actor, executor |
| `combat` | 공식 combat benchmark 확장 | PVP, Hawkeye와 combat setup; 필요한 상위 profile에 추가 |

`e0-executor`부터 `e2-actor-fixed`까지의 결과만으로 Odyssey 전체를 재현했다고 주장하지 않는다. `odyssey-legacy`와 `voyager-lifelong`도 서로 다른 논문 baseline으로 구분한다. `odyssey-full`은 공개 Odyssey 그대로가 아니라 능동 skill lifecycle을 복원한 확장 실험이다. 무거운 dependency라는 이유만으로 기능을 근거 없이 삭제하지 않고, 각 기능은 profile 간 통제 비교 후 배치 위치와 구현체를 결정한다.

## 7. 환경 구축 순서와 통과 기준

### Gate E0. 실행 계층 고정

목표: 모델 없이 Minecraft 행동 계층을 신뢰할 수 있게 만든다.

- [x] Docker image ID, Minecraft/Fabric/mod hash, Java, world seed와 Node dependency snapshot을 [`E0_test_evidence_2026-08-20.md`](./E0_test_evidence_2026-08-20.md)에 기록했다.
- [x] Node 20.13.1에서 E0 candidate의 `npm ci` 후 `npm ls --depth=0`이 exit code 0을 반환한다.
- [x] stale 하위 `node_modules` 없이 `npm ci` 직후 local collectblock build와 bridge 정적 검사를 재현했다.
- [x] `/health`와 bridge version 응답을 추가하고 bot 미접속 응답을 확인했다.
- [x] bot 접속 후 30초 동안 5초 간격 7개 표본에서 finite position을 유지했다.
- [x] raw 나무 채굴이 매회 hard reset·빈 인벤토리 조건에서 10/10 성공했다.
- [x] raw 작업대 제작이 매회 hard reset·빈 인벤토리 조건에서 10/10 성공했다.
- [x] `/pause`를 호출하지 않는 E0 raw 경로가 pause·iChunUtil·CompleteConfig·Fabric API 없는 Fabric server에서 연결·나무·작업대를 통과했다.
- [x] 자동 runner로 실행별 inventory before/after, error, wall-clock latency, health, dependency snapshot과 Minecraft log를 저장했다.

기존 `bot.craft` packet blocker, old/new bot lifecycle 경합, 실패 뒤 process-level exception crash, 새 offline server의 잘못된 OP UUID와 증거 자동화 문제를 모두 해소했다. E0의 기능 조건은 통과했으며 성공 commit/tag 고정만 남았다. node module 내부에는 patch를 누적하지 않는다.

### Gate E1. 최소 controller와 stub actor

목표: 모델 품질과 무관하게 endpoint·parser·registry·verifier 전체 경로를 검증한다.

- [ ] 고정 subgoal schema를 정의한다.
- [ ] candidate skill을 `mineWoodLog`, `craftCraftingTable`로 제한한다.
- [ ] deterministic stub endpoint를 만든다.
- [ ] strict JSON과 whitelist validation을 적용한다.
- [ ] inventory delta 기반 verifier를 일반 schema로 만든다.
- [ ] 동일 두 task를 각각 10회 통과한다.

### Gate E2. 실제 actor model 연결

목표: 파인튜닝 없이 model-in-the-loop 가능성을 확인한다.

- [ ] model adapter가 같은 `/v1/actor/select` 계약을 구현한다.
- [ ] 4B급 instruct model BF16 또는 공식 지원 precision으로 먼저 평가한다.
- [ ] JSON valid rate, candidate valid rate, skill top-1 accuracy를 offline에서 측정한다.
- [ ] 나무·제작대 online 성공률과 P50/P95 latency를 측정한다.
- [ ] 그 뒤에만 INT4 배포 정확도와 latency를 비교한다.

### Gate E3. Odyssey 기능을 한 개씩 복원

다음 기능은 각각 별도 profile/ablation으로 추가하고, 추가 전후 E0/E1 회귀 테스트를 반복한다.

1. deterministic candidate filter
2. 40 primitive + 183 compositional skill과 자연어 skill description 복원
3. 논문 조건의 Sentence Transformer query encoding과 top-5 similarity retrieval 복원
4. Chroma legacy 결과와 단순 in-memory vector search 결과 비교
5. planner/task decomposition
6. critic, execution feedback, failure reflection/replanning

E3는 고정된 223-skill corpus를 사용하는 공개 Odyssey baseline을 먼저 재현한다. 동적으로 library를 변경하지 않아 retrieval·actor·planner 오류를 skill 생성 오류와 분리한다.

Semantic retrieval 단계에서는 최소한 correct-skill recall@5, candidate coverage, retrieval latency, actor top-1 accuracy와 online task 성공률을 기록한다. original checkpoint·distance metric·top-k를 고정한 `odyssey-retrieval`을 먼저 보존한 뒤 encoder나 vector store를 바꾸는 실험을 수행한다.

각 구현체가 실험 성능이나 연구 질문에 기여하지 않으면 `mineskynet-core` 기본 profile에서 제외할 수 있다. 그러나 논문 핵심 기능을 제외한 결과를 원본 Odyssey 재현으로 보고하지 않으며, `odyssey-legacy` baseline은 별도로 유지한다.

### Gate E4. Voyager lifelong lifecycle과 Odyssey Full 확장

E0~E3 회귀가 고정된 뒤에만 능동적 skill 변경을 허용한다.

1. automatic curriculum이 현재 inventory·완료/실패 이력·보유 skill을 바탕으로 다음 과제를 제안한다.
2. strong model worker가 기존 skill과 primitive를 이용해 새 JavaScript 프로그램을 생성한다.
3. 환경 feedback, interpreter error와 critique를 이용해 제한 횟수 안에서 프로그램을 수정한다.
4. deterministic state delta와 self-verification이 모두 통과한 프로그램만 commit한다.
5. code, description, embedding, parent skill, model/prompt revision, world/commit 정보와 version을 원자적으로 저장한다.
6. 중복 이름 수정, vector index 동기화, rollback과 quarantine을 검증한다.
7. 새 world와 held-out task에서 생성 skill의 retrieval·재사용·전이 성능을 측정한다.

Full 단계의 핵심 지표는 verified-skill acceptance rate, false-accept rate, repair success rate, library growth, duplicate/conflict rate, retrieval recall@5, held-out reuse success와 skill 생성·검증 비용이다. arbitrary JavaScript는 E0~E3의 strict registry endpoint와 분리된 sandbox/quarantine 경로에서만 실행한다.

## 8. LoRA와 모델 연구의 Go/No-Go 기준

현재 Gemma 3 1B 실험은 “LoRA 학습 pipeline이 작동한다”는 것만 보였다. Minecraft QA 단일 질문과 training loss는 actor의 skill selection 또는 online task 성공 근거가 아니다.

LoRA를 다시 시작하는 조건은 다음과 같다.

1. E0와 E1이 모두 통과한다.
2. 파인튜닝하지 않은 실제 actor model의 baseline이 기록된다.
3. `observation + subgoal + candidate skills → skill_id` 형식의 actor 데이터와 누수 없는 test set이 존재한다.
4. 비교 metric을 JSON valid rate, candidate-valid rate, skill accuracy, Minecraft success rate, latency로 고정한다.

다음 중 하나면 LoRA를 중단한다.

- base model 대비 offline actor 정확도 개선이 없다.
- offline 개선이 online Minecraft 성공률로 이어지지 않는다.
- 4B급 base/quantized model이 이미 MVP task를 충분히 해결해 학습 비용 대비 이득이 작다.
- MoE 또는 특정 model architecture의 학습 지원 문제가 환경 구축 일정을 다시 막는다.

## 9. 즉시 실행할 작업

우선순위는 다음 세 단계다.

1. **E0 변경 고정**: 변경 범위를 검토해 성공 commit과 `mineskynet-e0-executor-1.19.4` tag를 만든다.
2. **minimal controller 분리**: `Odyssey()` 전체를 생성하지 않고 bridge에 fixed skill을 보내고 상태를 검증하는 실행 경로를 정식 MVP entrypoint로 만든다.
3. **E1 contract test**: deterministic stub, strict registry, 일반 delta verifier와 오류 taxonomy를 두 atomic task에서 검증한다.

이 세 단계가 끝나기 전에는 다음 작업을 보류한다.

- Gemma LoRA 추가 학습
- INT4 품질 비교
- embedding/Chroma 변경 또는 대체 실험
- planner/reflector 통합
- Tailscale 다중 노드 배포
- VillagerAgent 기반 orchestration

## 10. 재현성 체크리스트

- [ ] 각 서비스의 버전과 lockfile이 저장소에 존재한다.
- [ ] mutable Docker tag 대신 digest 또는 재현 가능한 image metadata를 기록한다.
- [ ] optional 기능은 lazy import/plugin profile로 분리한다.
- [ ] 논문 기능과 package 구현체의 대응표가 profile별로 존재한다.
- [ ] 환경 변수와 path는 repository-relative config로 관리한다.
- [ ] model weight, world data, cache는 Git 밖에 두되 revision/hash를 기록한다.
- [ ] `npm ci`, `npm ls`, `pip check`와 import smoke test가 자동화된다.
- [ ] health check가 Minecraft, bridge, actor service마다 존재한다.
- [ ] atomic test는 성공 메시지가 아니라 inventory/world-state 변화로 판정한다.
- [ ] failure는 timeout, connection, parse, invalid skill, execution, verification으로 구분한다.
- [ ] 실험 결과에는 commit, dependency snapshot, world seed와 로그 경로를 남긴다.
- [ ] retrieval 결과에는 encoder revision, distance metric, top-k, skill corpus hash와 recall@k를 남긴다.

## 11. 코드 근거

- 논문상 skill library, Sentence Transformer retrieval, planner–actor–critic 근거: [`research/paper/odyssey.pdf`](../paper/odyssey.pdf), Sec. 2.1–2.2 및 Sec. 5.3
- 전체 agent eager initialization: [`Odyssey/odyssey/odyssey.py`](../../Odyssey/odyssey/odyssey.py)
- embedding/Chroma 강제 초기화: [`agents/planner.py`](../../Odyssey/odyssey/agents/planner.py), [`agents/skill.py`](../../Odyssey/odyssey/agents/skill.py)
- actor parsing과 silent fallback: [`agents/actor.py`](../../Odyssey/odyssey/agents/actor.py)
- 동적 skill 저장 구현과 비활성화된 호출: [`agents/skill.py`](../../Odyssey/odyssey/agents/skill.py), [`odyssey.py`](../../Odyssey/odyssey/odyssey.py)
- custom LLM endpoint 호출: [`agents/llama.py`](../../Odyssey/odyssey/agents/llama.py)
- hard-coded subgoal verifier: [`agents/critic.py`](../../Odyssey/odyssey/agents/critic.py)
- Python–Node bridge와 pause 동작: [`env/bridge.py`](../../Odyssey/odyssey/env/bridge.py)
- plugin 일괄 로드: [`env/mineflayer/index.js`](../../Odyssey/odyssey/env/mineflayer/index.js)
- 현재 Node 의존성: [`env/mineflayer/package.json`](../../Odyssey/odyssey/env/mineflayer/package.json)
- 현재 Python 의존성: [`Odyssey/requirements.txt`](../../Odyssey/requirements.txt)
- Minecraft server profile: [`Odyssey/docker-compose.yml`](../../Odyssey/docker-compose.yml)
- raw atomic tests: [`smoke_test_mine_wood.py`](../../Odyssey/scripts/smoke_test_mine_wood.py), [`smoke_test_crafting_table.py`](../../Odyssey/scripts/smoke_test_crafting_table.py)
- legacy model service: [`LLM-Backend/main.py`](../../LLM-Backend/main.py), [`LLM-Backend/api/api.py`](../../LLM-Backend/api/api.py)
