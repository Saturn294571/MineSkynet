# MineSkynet 프로젝트 작업 보고 로그

> 문서 역할: 구현 과정에서 이미 보고한 내용과 당시의 완료·미완료 판단을 시간순으로 누적한다. 과거 보고는 후속 결과로 덮어쓰거나 삭제하지 않고, 새 검증 결과는 별도 보고 항목으로 추가한다. 목표와 다음 순서는 마일스톤에서 관리하고, 교수님께 제시할 내용은 `labmeeting_temp.md`에서 선별·편집한다. 각 단위 테스크당 보고 템플릿/예시는 아래와 같다. 불렛포인트(-)/번호 목록(1))/체크포인트([X])/표(|---|---|---|) 등은 이해를 돕기 위해 적절히 사용한다. 반드시 /home/pluto2479/Documents/MineSkynet/research/AGENTS.md 의 원칙을 준수하라.

```markdown
# MineSkynet 프로젝트 작업 보고 로그

## YYYY-MM-DD — 단위 테스크 제목 1

...

### n. 하위 테스크 이름

...

#### n.m. 하위 테스크의 세부사항 (논리상/분량상 구분할 필요가 있을경우)

...

## YYYY-MM-DD — 단위 테스크 제목 2

...

```

## 2026-08-19~20 — Odyssey 환경·의존성 진단과 현대화 범위 확정

작성일: 2026-08-19~20  
대상 코드: 공개 Odyssey와 당시 `experiment/mvp-core` 진단 환경

### 1. 논문상 기능과 진단 목적

Odyssey는 Minecraft environment에서 open-world skill library, semantic skill retrieval과 planner–actor–critic을 연결한다. 당시 가장 먼저 해결해야 할 문제는 model 성능이 아니라 Minecraft server → Mineflayer → JavaScript skill → state-based verification으로 이어지는 실행 고리를 안정화하는 것이었다.

원본 공개 코드는 작은 행동을 실행할 때에도 planner, critic, embedding model, Chroma, launcher와 model provider를 함께 초기화했다. 이 결합 때문에 오류가 어느 논문 기능에서 발생했는지 구분하기 어렵고, 사용하지 않는 legacy dependency까지 모든 환경에 설치해야 했다.

문제를 분리하기 위해 E0~E4 gate를 임시 진단 도구로 사용했다. 이 gate는 결함 격리 과정의 역사적 이름이며, 이후 MineSkynet 연구 개발 순서나 최종 연구 기여로 사용하지 않는다.

### 2. 진단에서 확정한 원칙

#### 2.1 논문 기능과 실행환경의 분리

Planner–actor–critic, semantic retrieval과 skill library는 보존해야 할 Odyssey의 논문 기능이다. 반면 Multiplayer Server Pause bundle, launcher와 특정 model provider SDK는 특정 실행 방식에 필요한 dependency이므로 profile로 격리할 수 있다.

따라서 기본 profile에서 비활성화하는 것과 연구 시스템에서 기능을 제거하는 것을 구분한다.

#### 2.2 현대화의 연구 범위 제한

Odyssey 현대화의 목적은 legacy보다 빠르거나 우수함을 증명하는 것이 아니라, 구형 dependency issue로부터 안전한 MineSkynet 실험 기반을 만드는 것이다. `master`는 논문 기능과 공개 구현을 확인하는 source reference로 사용하며 legacy runtime의 성공률·latency 재측정은 완료 조건으로 삼지 않는다.

#### 2.3 신뢰받는 외부 구현의 보존

Sentence Transformer, Chroma와 LangChain은 semantic retrieval의 서로 다른 기능을 담당한다. 구형 API와 지원 조합은 갱신할 수 있지만, 이들을 근거 없이 자체 구현으로 교체하지 않는다. 변경 전후에 동일 corpus의 index 생성·재로드와 candidate retrieval contract를 먼저 보존한다.

#### 2.4 Model 성공과 embodied agent 성공의 구분

Minecraft 질문에 답하거나 training loss가 감소하는 것은 Actor가 올바른 skill을 선택해 environment state를 바꿨다는 증거가 아니다. Model 평가는 candidate-valid selection과 실제 Minecraft state delta까지 연결해야 한다.

### 3. 교수 피드백과 현재 해석

| 과거 피드백 | 현대화에 남긴 원칙 |
|---|---|
| 환경 설정이 최우선 | model·분산 연구 전에 반복 가능한 executor와 state verification을 확보한다. |
| 최소 dependency만 유지 | 기능을 삭제하지 않고 executor, retrieval, model, launcher, combat와 training profile을 분리한다. |
| 작은 model의 성능이 부족할 수 있음 | local model은 자유 계획·code generation보다 bounded skill selector부터 평가한다. |
| LoRA의 의미가 약하면 중단 | zero-shot/base model과 동일 task에서 비교하고 online 성공 개선이 없으면 학습을 연구 핵심에서 제외한다. |
| 새 기억이 기존 능력을 훼손할 수 있음 | 기본 MineSkynet Actor는 read-only registry를 사용하고 능동 skill lifecycle은 별도 Voyager/Full profile에서 검증한다. |
| 복잡한 문제를 더 복잡하게 만들지 말 것 | 한 고리씩 격리하되 component smoke를 전체 시스템 완료로 표기하지 않는다. |

### 4. E0 실행 계층에서 먼저 확인한 결과

Model 없이도 기존 Odyssey skill이 modernized Mineflayer 환경에서 반복 실행되고, failure 뒤 bridge가 다시 요청을 받을 수 있는지 확인했다.

- Minecraft `1.19.4`, Java `17`, Node `20.13.1` 조합 고정
- Mineflayer `4.25.0`과 관련 Prismarine dependency를 lockfile에 고정
- `/pause` 없는 mod-free server에서 raw 원목 채집과 작업대 제작을 각각 10/10 통과
- chat message가 아니라 inventory delta로 success 판정
- 잘못된 연결, 연속 reset과 의도적 skill error 뒤 bridge recovery 확인
- 실행 계층 결과를 commit `a157205`와 tag `odyssey-modernized-executor-1.19.4`로 고정

이 결과는 Minecraft execution layer의 범위이며 Odyssey 전체 논문 환경 재현을 뜻하지 않는다. 환경 snapshot과 반복 결과는 바로 다음 E0 증거 보고에 상세히 기록한다.

### 5. 실행 계층에서 분리·해결한 결합

| 문제 | 연구자가 이해할 한 줄 의미 | 처리 |
|---|---|---|
| Multiplayer Server Pause bundle | model 응답을 기다리는 동안 world를 멈추는 legacy 장치이며 raw skill 실행에는 필요하지 않음 | modernized executor 기본 경로에서 제외하고 Python legacy adapter에만 남김 |
| global bot lifecycle | 이전 bot의 늦은 종료가 새 bot까지 종료해 서로 다른 request의 상태가 섞임 | request-local bot과 identity check 적용 |
| non-finite motion | chunk 준비 전 physics가 잘못된 position packet을 보낼 수 있음 | chunk readiness와 finite-state guard 적용 |
| offline operator UUID | 새 world에서 bot이 reset command 권한을 얻지 못함 | 재현 가능한 offline UUID profile 고정 |
| mutable Node dependency tree | 설치 시점마다 protocol·physics dependency 조합이 달라질 수 있음 | exact package-lock과 health/version response 고정 |

### 6. E0 이후 다시 연결할 논문 기능

다음 기능은 E0에서 제거한 것이 아니라 modernized Odyssey에 다시 연결해야 할 범위로 남겼다.

- 40 primitive + 183 compositional skill corpus
- Sentence Transformer 기반 description/query embedding
- top-5 기본·top-10 별도 profile의 semantic retrieval
- MineMA Actor의 exact candidate selection
- recursive prerequisite execution
- planner–actor–critic feedback과 replanning
- 논문 benchmark의 task·prompt·success condition

Voyager의 curriculum, code generation/repair와 dynamic skill commit도 삭제하지 않는다. 공개 Odyssey의 fixed-library baseline과 분리해 `voyager-lifelong`과 `odyssey-full` profile에서 보존한다.

### 7. 당시 상태와 해석

E0~E4 gate는 dependency 결함을 격리하는 데 유용했지만, 각 gate의 최소 통과를 연구 목표로 확대해서는 안 된다고 판단했다. 이후에는 “원본 논문 기능을 재현하되 불안정하거나 비효율적인 dependency 고리를 제거·대체·업데이트한다”는 방향으로 마일스톤을 재편했다.

### 8. 근거 파일

- [원본 환경·의존성 진단 문서](MVP_report.md)
- [E0 원시 증거](E0_test_evidence_2026-08-20.md)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)
- [논문–코드–dependency 대응표](paper_code_dependency_map.md)

## 2026-08-20 — E0 Minecraft execution layer 검사 증거

작성일: 2026-08-20  
검사 profile: `e0-executor` 후보 환경

### 1. 논문상 기능과 증거 범위

이 검사는 model과 Planner를 제외하고, Actor가 선택할 JavaScript skill을 Mineflayer가 실제 Minecraft state change로 실행할 수 있는지 확인했다. 구체적으로 raw Odyssey skill의 반복 실행, inventory delta 기반 success 판정과 failure 이후 bridge recovery를 검증했다.

이는 Odyssey의 Minecraft execution layer에 대한 증거이며 semantic retrieval, MineMA Actor와 planner–actor–critic 전체 재현을 의미하지 않는다. 원시 world와 cache는 Git 밖의 `Odyssey/runtime/`에 유지했다.

### 2. 환경 snapshot

- Git 기준 commit: `80a42fcbd2b5da53ecf7e58f1036981e428c9590` (`origin/experiment/mvp-core`); 검사 시점에는 E0 관련 uncommitted change가 존재
- Docker image: `itzg/minecraft-server:java17`
- image ID: `sha256:5b3e96bcd7dace8ab7be89c245dc9ba0b1573fdef2f01d3e101ac40e7843fa70`
- Minecraft `1.19.4`, Fabric Loader `0.15.11`, Java `17.0.15+6`
- world seed: `7634567288700934061`
- Node `20.13.1`, npm `10.5.2`
- offline-mode bot operator UUID: `67128b5b-2e6b-3ad1-baa0-1b937b03e5c5` (`OfflinePlayer:bot`)
- operator profile: `Odyssey/server-profile/e0/ops.json`
- `package-lock.json` SHA-256: `5555e896e0c5d19c635965bc9338b0cd60a248092bc9c8ff65a6c678943a6b7c`

직접 Node dependency는 다음 조합으로 고정했다.

| Dependency | Version |
|---|---:|
| mineflayer | 4.25.0 |
| minecraft-data | 3.83.0 |
| mineflayer-pathfinder | 2.4.2 |
| mineflayer-tool | 1.2.0 |
| local mineflayer-collectblock | 1.4.1 |
| express | 4.18.2 |
| vec3 | 0.1.8 |
| typescript | 4.9.5 |
| @types/node | 18.19.130 |
| prismarine-entity | 2.4.0 |
| prismarine-item | 1.15.0 |

`npm ci` 감사에서는 16 vulnerabilities(3 low, 6 moderate, 7 high)가 보고됐다. 호환성이 검증된 묶음을 임의 변경하지 않기 위해 `npm audit fix`는 실행하지 않고 warning과 영향 범위를 후속 관리 대상으로 남겼다.

#### 2.1 기존 optional mod bundle snapshot

| JAR | Version | SHA-256 |
|---|---:|---|
| Multiplayer Server Pause | 1.3.1 | `fe6fe7e5c398415578f2be355de4bcd74ed5f11ebb5929d1aa91381fa8074d24` |
| CompleteConfig | 2.3.1 | `f7d5c7c82df363305b726f6fad651a68dad8404322d4b7a0f46d948882affcc2` |
| Fabric API | 0.87.2+1.19.4 | `a92650d48a9f672dc74e8b1eaefedb28dc83a13a80431215900181aa3a8675d8` |
| iChunUtil | 1.0.2 | `661b800c180d8f0dfca2467bebfbd57c41cd6b9e22cac989fb8979e3137d6475` |

이 JAR은 legacy pause fixture의 snapshot이며 mod-free raw executor의 필수 dependency로 판정하지 않았다.

### 3. Dependency와 interface 정적 검사

1. 활성 dependency tree에서 과거 `mineflayer-collectblock/node_modules`를 분리한 뒤 `npm ci`가 성공했다.
2. `npm run check`가 local collectblock TypeScript build, `node --check index.js`, `npm ls --depth=0`을 모두 통과했다. `npm ci` 뒤에도 하위 `mineflayer-collectblock/node_modules`는 생성되지 않았다.
3. `/health`와 `/version`은 pinned Minecraft `1.19.4`와 dependency version을 반환했다.

### 4. Minecraft runtime 반복 결과

#### 4.1 Connection과 finite state

Modded fixture에서 bot 연결과 finite position을 0·5·10·15·20·25·30초에 확인해 7/7 통과했다. Clean `npm ci` 직후에도 30초 연결, 원목 1회와 작업대 1회를 다시 실행해 모두 통과했다.

#### 4.2 Raw skill state delta

매회 hard reset과 empty inventory로 두 raw skill을 각각 10회 실행했다.

| Raw skill | 반복 | Before | After | State-based success | Error |
|---|---:|---|---|---|---|
| `mineWoodLog` | 10/10 | `{}` | `spruce_log: 1` | log delta `+1` | `onError: []` |
| `craftCraftingTable` | 10/10 | `{}` | `crafting_table: 1` | table delta `+1` | `onError: []` |

`Odyssey/scripts/e0_regression.py`로 기존 fixture에서 두 작업을 다시 실행한 최종 회귀도 총 20/20, 모든 목표 delta `+1`, 모든 `onError: []`로 통과했다.

#### 4.3 Mod-free executor

별도 임시 Fabric server는 같은 image ID, Minecraft version, Fabric Loader와 seed를 사용하되 외부 mod JAR를 넣지 않았다. Server log의 mod 목록은 Minecraft, Java, Fabric Loader와 내장 MixinExtras뿐이었다.

이 server에 `soft`로 접속해 finite position 30초, 원목 채집과 empty inventory의 작업대 제작을 각각 통과했다. 실행 경로는 `/health`, `/start`, `/step`만 호출하고 `/pause`를 호출하지 않았다. 따라서 raw E0 execution에는 Multiplayer Server Pause, iChunUtil, CompleteConfig와 Fabric API가 필요하지 않음을 확인했다.

### 5. Failure recovery와 bot lifecycle

`/start`가 request별 bot instance를 capture하도록 수정하고 pending start response와 old-bot disconnect를 분리했다. 다음 recovery fixture를 통과했다.

- 연속 hard `/start` 2회 뒤 새 bot 15초 생존
- 잘못된 port의 400 response 뒤 bridge 생존 및 정상 hard reset recovery
- 의도적인 `/step` JavaScript error 뒤 connection 유지
- request-local process exception listener 정리 뒤 다음 request 수신

새 offline-mode server에서는 `OPS=bot`이 online UUID를 기록해 hard reset timeout을 일으키는 문제를 확인했다. 올바른 offline UUID를 담은 `OPS_FILE`을 Compose에 고정한 뒤 외부 mod 없는 새 server의 첫 번째·두 번째 hard reset, 15초 finite position, 원목과 작업대를 모두 통과했다.

### 6. Latency 관찰값

| Raw skill | 평균 action latency | P95 action latency |
|---|---:|---:|
| `mineWoodLog` | 10,829.307 ms | 20,384.104 ms |
| `craftCraftingTable` | 13,172.842 ms | 23,990.514 ms |

Latency는 modernized가 legacy보다 빠르다는 비교 증거가 아니라, 당시 반복 실행의 환경 관찰값으로만 보존한다.

### 7. 해결한 결함과 증거 위치

- old bot의 늦은 disconnect가 새 global bot을 종료하던 race를 request-local bot capture와 identity check로 해결했다.
- `/step` process-level exception listener가 request-local bot을 사용하고 response `finish`/`close`에서 정리되게 했다.
- 새 offline server의 hard reset timeout 원인을 잘못된 online OP UUID로 식별하고 Compose가 traceable offline UUID `OPS_FILE`을 사용하게 했다.
- 최종 raw 결과는 `Odyssey/odyssey/env/results/e0/20260820T021925+0900/`에 저장했다. `environment.json`, 실행별 JSON 20개, `summary.json`, `minecraft_latest.log`를 포함하며 local runtime 결과라 Git에서 제외된다.
- 검사 당시에는 success commit/tag를 만들지 않았고, 이후 변경을 `a157205` (`E0 finished`)에 commit한 뒤 `odyssey-modernized-executor-1.19.4` annotated tag로 local·remote에 고정했다.

### 8. 당시 상태와 해석

Minecraft execution layer는 clean install, raw action success와 대표 failure recovery를 반복 통과했다. 이 결과로 model·retrieval과 분리된 mod-free executor baseline을 확보했다. 다만 E0는 Odyssey 전체 재현이 아니며, semantic retrieval, Actor selection, recursive prerequisite와 planner–actor–critic은 별도 component 검증으로 남았다.

### 9. 근거 파일

- [원본 E0 검사 증거](E0_test_evidence_2026-08-20.md)
- [E0 regression script](../../Odyssey/scripts/e0_regression.py)
- [E0 server profile](../../Odyssey/server-profile/e0/ops.json)
- [환경·dependency 진단 기록](MVP_report.md)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)

---

## 2026-08-27 — Primitive runtime 결함 정리

작성일: 2026-08-27  
대상 브랜치: `experiment/odyssey-modernized`

### 1. 논문상 기능과 작업 범위

Odyssey의 open-world skill library는 40개 primitive skills와 183개 compositional skills로 구성된다. Primitive skills는 Mineflayer JavaScript API 위에서 parameterized input을 받는 foundational interfaces이며, compositional skill이 더 복잡한 task와 prerequisite를 재귀적으로 수행할 때 사용하는 저수준 실행 단위다. 논문은 시각 입력이 없는 환경에서 precise positioning과 orientation을 담당하는 spatial skills가 특히 중요하다고 설명한다.

이번 작업은 Odyssey-added spatial primitive 가운데 `goto`와 `getAnimal`을 대상으로 했다.

- `goto`: 지정 좌표의 허용 오차 안으로 bot을 이동시킨다.
- `getAnimal`: 동물 종류에 맞는 먹이를 들고 해당 동물을 지정 좌표까지 유인한다.

목적은 두 함수를 새 행동으로 대체하는 것이 아니라, compositional skill이 호출했을 때 조용히 성공하거나 무한 대기하지 않고 논문상 primitive contract를 실제 Minecraft state로 확인할 수 있게 하는 것이었다.

### 2. 확인한 결함

| Primitive | 공개 코드 결함 | 논문 기능에 미치는 영향 |
|---|---|---|
| `goto` | `bot.entity.positon` 오타 | 현재 위치를 읽을 수 없어 이동 contract 실행 불가 |
| `goto` | x·y·z 세 축이 모두 오차를 벗어날 때만 반복하는 조건 | 한 축만 멀어도 성공으로 종료할 수 있음 |
| `goto` | timeout과 최종 위치 검증 부재 | pathfinder 정지·부분 이동을 성공과 구분하기 어려움 |
| `getAnimal` | `type = "sheep"` 형태의 대입 조건과 항상 참인 `|| "cow"` | 입력 animal type과 무관하게 잘못된 먹이 분기로 진입 |
| `getAnimal` | `chichken` 오타와 입력·먹이 검증 부재 | chicken branch와 failure 원인을 신뢰할 수 없음 |
| `getAnimal` | 동물을 찾은 뒤 target으로 bot만 이동 | 동물이 실제 target까지 따라왔는지 확인하지 않음 |

### 3. 수정 내용

`goto`는 finite coordinate와 positive timeout을 검사하고, Mineflayer pathfinder의 `GoalNear`를 사용해 반경 2블록 안으로 이동하게 했다. 이동 전·후 위치를 검사하고 timeout이나 pathfinder failure가 발생하면 goal을 취소한 뒤 `[goto]` 오류로 반환한다.

`GoalNear`는 실수 좌표를 Minecraft block-grid로 내림해 반경을 계산한다. 따라서 초기 구현처럼 실수 target과 bot 중심 사이의 Euclidean distance를 후조건으로 사용하면 pathfinder는 성공했는데 primitive가 실패하는 불일치가 생긴다. 최종 contract는 `GoalNear`와 동일한 block-grid distance 2 이하로 통일했다.

`getAnimal`은 animal–food mapping을 다음과 같이 명시했다.

- sheep·cow → wheat
- chicken → wheat seeds
- pig → carrot

지원하지 않는 animal type, 먹이 부재, 32블록 안에서 animal을 찾지 못한 경우를 명시적 오류로 분리했다. 동물을 찾으면 먼저 접근해 바라보고, 먹이를 든 상태에서 `goto`로 target까지 이동한 뒤 animal이 target 반경 4블록 안에 들어왔는지 최대 100 tick 동안 확인한다.

### 4. Offline fixture 결과

mock bot과 pathfinder를 사용한 state-based fixture 14개가 모두 통과했다.

- `goto` 6개: 이미 반경 안인 경우, 정상 GoalNear 이동, 실제 실패 좌표의 block-grid 회귀, 비정상 좌표, timeout·goal 취소, target 미도달 실패
- `getAnimal` 8개: 네 animal–food mapping, 지원하지 않는 type, 먹이 부재, animal 탐색 실패, target까지 따라오지 않는 경우

```text
14/14 primitive offline fixtures passed
```

### 5. Minecraft online fixture 결과

`getAnimal(cow)`은 bot 근처에 cow 한 마리와 wheat를 준비하고 현재 위치에서 x축 8블록 떨어진 target까지 유인했다. 최종 bot–target 거리는 약 `0.842`, cow–bot 거리는 약 `2.223`이었고 `onError` 없이 통과했다.

`goto` 첫 실행은 6블록 이동 뒤 실수 target 거리 `2.154`에서 primitive 오류를 반환했다. 그러나 이는 pathfinder 이동 실패가 아니라 `GoalNear`의 block-grid 반경과 실수 좌표 후조건의 불일치였다. 실제 관측 좌표를 offline regression fixture에 추가하고 contract를 통일한 뒤 다시 실행했다.

재실행에서는 다음 결과로 통과했다.

```text
bot_distance_to_target: 1.3954
bot_block_distance_to_target: 1.4142
onError: []
PASS: goto state-based online fixture
```

### 6. 당시 상태와 해석

`goto`와 `getAnimal`은 offline 14/14와 실제 Minecraft online fixture를 통과했다. 이는 두 spatial primitive의 contract를 확인한 component 결과이며 primitive 40개 전체 또는 Odyssey end-to-end 재현 완료를 뜻하지 않는다. 나머지 primitive contract와 Voyager-inherited interface fixture는 후속 검증으로 남겼다.

### 7. 근거 파일

- [Primitive 40 working manifest](../manifest/odyssey_primitive_40.json)
- [Offline primitive fixture](../../Odyssey/scripts/primitive_runtime_offline.js)
- [Online primitive fixture](../../Odyssey/scripts/primitive_runtime_online.py)
- [실행 절차](../README.md#37-primitive-runtime-online-fixture)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)

---

## 2026-08-27 — Semantic encoder 조건 고정

작성일: 2026-08-27  
대상 브랜치: `experiment/odyssey-modernized`

### 1. 논문상 기능과 이번 작업의 목적

Odyssey의 LLM Actor는 Planner가 생성한 text-based subgoal을 바로 실행 코드로 바꾸지 않는다. 먼저 subgoal을 **query context**로 encoding하고, open-world skill library에 저장된 **skill description**과의 vector similarity를 계산해 **semantic closeness**가 높은 skill을 retrieval한다. Actor는 이렇게 제시된 top-5 relevant skills 중 subgoal 실행에 가장 적절한 code를 선택한다.

Skill library 쪽에서는 각 skill의 complete program code를 바탕으로 자연어 description을 생성하고, Sentence Transformer가 이 description을 vector representation으로 변환한다. 따라서 semantic encoder는 다음 두 입력을 같은 의미 공간에 배치하는 논문 기능이다.

- Planner가 생성한 자연어 subgoal: retrieval의 query context
- 183개 compositional skill의 자연어 description: 검색 대상 corpus

이번 작업의 목적은 이 논문 기능을 제거하거나 자체 구현으로 대체하는 것이 아니라, 공개 Odyssey 코드가 사용한 Sentence Transformer의 checkpoint와 text-to-vector 변환 조건을 명시적으로 고정해 dependency 변경 뒤에도 같은 semantic skill retrieval을 재현할 수 있게 하는 것이다.

### 2. 감사에서 확인한 재현 위험

논문은 Sentence Transformer를 통한 query context encoding과 skill similarity retrieval을 설명하지만 정확한 checkpoint 이름은 명시하지 않는다. 반면 공개 코드의 `conf/config.json`은 `paraphrase-multilingual-MiniLM-L12-v2`를 지정한다. 따라서 이 모델은 **논문이 명시한 checkpoint가 아니라 공개 코드가 선택한 modernized 재현 기준**으로 구분해야 한다.

또한 기존 구현은 `HuggingFaceEmbeddings(model_name=...)`에 model 경로만 전달했다. 이 상태에서는 normalization, precision과 batch 설정이 설치된 Sentence Transformers·LangChain 버전의 기본값에 의존한다. 동일 model 파일을 사용하더라도 dependency 변화가 vector scale이나 retrieval score에 영향을 줄 가능성이 있었다.

마지막으로 `SkillManager`의 기본 retrieval 수는 5였지만 상위 `Odyssey` 생성자의 기본값은 10으로 남아 있어, 논문 본문의 top-5 skill selection 및 현재 profile 정책과 실제 runtime 기본값이 일치하지 않았다.

### 3. 수행 내용

#### 3.1 공개 코드 checkpoint의 provenance 고정

modernized baseline의 model ID를 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`로 기록하고, 로컬 Hugging Face download metadata에서 revision을 다음과 같이 확인했다.

```text
e8f8c211226b894fcb81acc59f3b34ba3efd5f42
```

로컬 model directory에는 PyTorch, ONNX, OpenVINO와 TensorFlow용 중복 artifact가 함께 존재한다. 현재 Odyssey의 Sentence Transformer 실행에는 PyTorch safetensors 경로를 사용하므로, `model.safetensors`와 tokenizer·pooling·model config 등 runtime에 필요한 11개 파일만 canonical artifact로 정하고 각각의 크기와 SHA-256을 manifest에 기록했다. 사용하지 않는 변환·양자화 artifact는 재현 checksum 범위에서 제외했다.

#### 3.2 Query context와 skill description의 encoding 조건 고정

checkpoint 내부 설정과 현재 adapter 동작을 대조해 다음 text-to-vector contract를 고정했다.

| 항목 | 고정값 | 논문 기능상 의미 |
|---|---:|---|
| vector dimension | 384 | query context와 skill description을 비교하는 공통 vector representation |
| maximum sequence length | 128 tokens | 긴 text 입력이 잘리는 동일한 경계 |
| pooling | attention-mask-aware mean pooling | token representation을 하나의 sentence representation으로 결합 |
| case folding | 사용하지 않음 | 입력 대소문자를 임의로 변경하지 않음 |
| normalization | 사용하지 않음 | 기존 공개 adapter의 vector scale을 보존 |
| precision | float32 | canonical embedding 계산 정밀도 |
| batch size | 32 | corpus encoding의 기본 처리 단위 |
| adapter preprocessing | newline을 ASCII space로 치환 | query와 description에 동일한 text 전처리 적용 |

query와 document는 서로 다른 encoder를 사용하지 않는다. LangChain adapter의 `embed_query`가 document encoding 경로를 공유하도록 유지해, subgoal과 skill description이 동일한 model·pooling·normalization 조건에서 비교되게 했다.

#### 3.3 Skill retrieval과 Planner QA retrieval의 encoder 설정 통일

기존에는 `SkillManager`와 `PlannerAgent`가 각각 `HuggingFaceEmbeddings`를 직접 생성했다. 두 경로가 dependency update 과정에서 서로 다른 설정을 갖지 않도록 공통 factory인 `odyssey/retrieval_embedding.py`를 추가했다.

두 retrieval 경로는 이제 다음 값을 명시적으로 공유한다.

- `normalize_embeddings=False`
- `precision="float32"`
- `batch_size=32`
- progress output 비활성화

또한 `Odyssey` runtime의 기본 skill retrieval 수를 논문 본문과 결정된 profile에 맞춰 top-5로 수정했다. top-10은 제거하지 않고 autonomous exploration 등을 위한 별도 retrieval profile로 남겨, 다음 단계에서 동일 corpus와 distance metric을 사용한 회귀 fixture로 검증한다.

#### 3.4 재현 manifest와 fixture 작성

`odyssey_semantic_encoder.json`에 model provenance, canonical artifact checksum, transformation contract, 관찰된 dependency version과 top-k 정책을 기록했다.

`semantic_encoder_fixture.py`는 두 단계로 실행된다.

1. **Static contract fixture:** model inference 없이 revision, 11개 artifact checksum, vector dimension, maximum sequence length, pooling과 source의 명시적 설정을 검사한다.
2. **Runtime contract fixture:** CPU에서 고정된 한국어·영어 문장을 실제로 encoding해 `(3, 384)` shape, NaN/Inf 부재, 반복 실행 오차와 newline/space 전처리 동등성을 검사한다.

현재 static contract fixture는 모든 항목을 통과했다. 실제 embedding runtime fixture는 연구자 실행 전이므로 semantic encoder 전체를 완료로 표시하지 않았다.

### 4. 당시 상태와 해석

| 논문상의 단계 | 당시 확보한 근거 | 상태 |
|---|---|---|
| skill description을 vector representation으로 변환 | checkpoint·pooling·전처리·artifact checksum 고정 | 정적 검증 완료 |
| text-based subgoal을 query context로 encoding | skill description과 동일한 공통 encoder factory 적용 | 정적 검증 완료 |
| query context와 skill description의 similarity matching | distance metric과 실제 candidate 순위 미확정 | 다음 단계 |
| top-5 relevant skills 제시 | runtime 기본값을 top-5로 통일 | 정책·코드 반영 완료 |
| Actor가 적절한 code 선택 | MineMA Actor 연결 전 | 범위 밖·후속 단계 |

즉, 이 시점의 결과는 Odyssey의 semantic skill retrieval 전체 성공이 아니라, retrieval 입력을 생성하는 **semantic encoder 조건을 반복 가능한 상태로 고정한 것**이다. top-5/top-10 후보 결과, vector-store persist/reload와 Actor의 최종 skill selection은 별도 검증으로 남아 있었다.

### 5. 당시 다음 확인 작업

Minecraft server, Mineflayer bridge와 MineMA backend 없이 다음 명령을 연구자 실행 단계로 남겼다.

```bash
cd ~/Documents/MineSkynet
Odyssey/.venv/bin/python Odyssey/scripts/semantic_encoder_fixture.py --run-model --device cpu
```

당시 통과 기준은 세 입력의 384차원 vector 출력, finite 값, 반복 encoding 최대 절대 오차 `1e-6` 이하, newline/space 입력 동등성과 마지막 `PASS` 출력이었다. 이 실행 결과를 확보한 뒤 embedding checksum·vector norm과 현재 dependency 조합을 manifest에 기록하기로 했다.

### 6. 당시 근거 파일

- [Semantic encoder manifest](../manifest/odyssey_semantic_encoder.json)
- [Semantic encoder fixture](../../Odyssey/scripts/semantic_encoder_fixture.py)
- [공통 retrieval encoder 설정](../../Odyssey/odyssey/retrieval_embedding.py)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)
- [논문–코드–dependency 대응표](paper_code_dependency_map.md)

---

## 2026-08-27 — Semantic encoder runtime 및 top-5 retrieval 추가 보고

작성일: 2026-08-27  
대상 브랜치: `experiment/odyssey-modernized`

### 1. 추가 확인 목적

최초 보고에서 미실행으로 남긴 CPU encoder fixture를 수행하고, 고정한 checkpoint와 183개 skill description으로 논문의 query context encoding → similarity matching → top-5 relevant skills 흐름이 실제 동작하는지 확인했다.

### 2. Semantic encoder runtime 결과

CPU runtime fixture에서 세 입력이 `(3, 384)` float32 vector로 변환됐고, NaN/Inf가 없으며 반복 실행과 newline/space 입력의 최대 절대 오차가 모두 `0.0`임을 확인했다. 고정 입력 embedding의 SHA-256은 `4f5de76040931c0558f63c1e6083f6779c61f1611b81f9d456aa9b7263d32c6b`이다.

### 3. Semantic skill retrieval smoke test

기존 문서와 로그에는 query 원문, candidate 이름과 score가 함께 남은 실행 증거가 없었다. 따라서 고정한 encoder로 `skills.json`의 183개 skill description을 모두 Chroma에 indexing하고, 논문의 query context encoding → similarity matching → top-5 relevant skills 흐름을 직접 실행했다.

| Text-based subgoal/query context | 기대 skill | top-1 결과 | L2 score |
|---|---|---|---:|
| `Craft a wooden pickaxe.` | `craftWoodenPickaxe` | `craftWoodenPickaxe` | 16.1350 |
| `Mine diamond ore using an iron pickaxe.` | `mineDiamond` | `mineDiamond` | 11.6207 |
| `Breed two cows using wheat.` | `breedCow` | `breedCow` | 25.7432 |
| `밀을 사용해서 소 두 마리를 번식시킨다.` | `breedCow` | `breedCow` | 16.0217 |

183개 description이 모두 index에 들어갔고, 네 query 모두 기대 skill이 top-5에 포함됐을 뿐 아니라 rank 1로 반환됐다. 이 smoke set의 known-query recall@5는 `4/4 = 1.0`이다. 따라서 현재 고정 checkpoint와 corpus로 **실제 semantic skill retrieval이 가능하다**고 보고할 수 있다. 이는 네 개의 대표 query에 대한 기능 smoke 결과이며 전체 skill corpus의 일반적인 retrieval 정확도를 의미하지는 않는다.

표의 L2 score는 확률이나 정확도가 아니라 query vector와 description vector 사이의 거리이며, 같은 profile 안에서는 값이 작을수록 더 가까운 candidate다.

실행 중 다음 현대화 경고도 관찰했다.

- LangChain의 기존 `HuggingFaceEmbeddings` wrapper가 `langchain-huggingface`로 이전 예정이라는 deprecation 경고
- LangChain의 기존 Chroma wrapper가 `langchain-chroma`로 이전 예정이라는 deprecation 경고
- Chroma telemetry의 `capture()` signature 불일치 경고

세 경고는 이번 indexing과 candidate retrieval을 중단시키지 않았다. 그러나 구형 dependency issue로부터 안전한 실행환경을 만들기 위해 wrapper 지원 조합과 telemetry 설정은 후속 작업에서 정리해야 한다.

### 4. 현재 상태와 해석

| 논문상의 단계 | 현재 확보한 근거 | 상태 |
|---|---|---|
| skill description을 vector representation으로 변환 | 183개 description 전체 indexing | runtime 검증 완료 |
| text-based subgoal을 query context로 encoding | 영어 3개·한국어 1개 query 실제 encoding | runtime 검증 완료 |
| query context와 skill description의 similarity matching | L2 top-5 candidate와 score 기록 | smoke 검증 완료 |
| top-5 relevant skills 제시 | 기대 skill rank 1: 4/4, recall@5: 1.0 | smoke 검증 완료 |
| Actor가 적절한 code 선택 | MineMA Actor 연결 전 | 범위 밖·후속 단계 |

즉, semantic encoder 조건 고정을 넘어 183개 공개 skill corpus에서 top-5 semantic retrieval이 실제로 동작함을 확인했다. 다만 이것은 제한된 known-query smoke test이며, 별도 top-10 profile, index persist/reload 뒤 candidate 순서 유지와 Actor의 최종 skill selection은 검증하지 않았다.

### 5. 재현 명령과 남은 작업

Minecraft server, Mineflayer bridge와 MineMA backend 없이 다음 명령으로 encoder와 top-5 retrieval 결과를 각각 재현할 수 있다.

```bash
cd ~/Documents/MineSkynet
Odyssey/.venv/bin/python Odyssey/scripts/semantic_encoder_fixture.py --run-model --device cpu
Odyssey/.venv/bin/python Odyssey/scripts/semantic_retrieval_smoke.py
```

두 fixture는 2026-08-27 CPU 실행에서 통과했다. 다음에는 같은 corpus·encoder·metric에서 top-10을 별도 profile로 실행하고, 저장한 Chroma index를 다시 열어도 candidate 순서가 유지되는지 확인한다. LangChain embedding/Chroma wrapper의 deprecated API와 telemetry warning도 기능 회귀를 유지하면서 정리해야 한다.

### 6. 추가 보고 근거 파일

- [Semantic encoder manifest](../manifest/odyssey_semantic_encoder.json)
- [Semantic encoder fixture](../../Odyssey/scripts/semantic_encoder_fixture.py)
- [Semantic retrieval smoke fixture](../../Odyssey/scripts/semantic_retrieval_smoke.py)
- [Semantic retrieval 실행 로그](../log/semantic_retrieval_smoke_2026-08-27.json)
- [공통 retrieval encoder 설정](../../Odyssey/odyssey/retrieval_embedding.py)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)
- [논문–코드–dependency 대응표](paper_code_dependency_map.md)

---

## 2026-08-27 — Retrieval fixture 완성

작성일: 2026-08-27  
대상 브랜치: `experiment/odyssey-modernized`

### 1. 논문상 기능과 이번 작업의 목적

Odyssey는 Planner의 text-based subgoal을 query context로 encoding하고, open-world skill library의 description vector와 similarity matching해 relevant skills를 Actor에게 제시한다. 이번 작업은 이 semantic skill retrieval을 다음 두 실행 profile과 반복 가능한 vector-store contract로 고정하는 것이 목적이다.

- 기본 `top5`: 논문 본문의 Actor candidate selection 조건이자 연산 부담을 줄인 기본 profile
- 별도 `top10`: 부록과 autonomous exploration 조건을 보존하는 확장 profile

검증 대상은 자연어 subgoal → 183개 description index → 순서와 score를 가진 candidate 반환까지다. MineMA Actor의 최종 선택과 Minecraft skill 실행은 이번 fixture의 범위가 아니다.

### 2. 구현한 retrieval contract

공통 retrieval 설정에 `top5=5`, `top10=10` profile과 기본 profile `top5`를 명시했다. `SkillManager`와 상위 `Odyssey` 생성자는 이 기본값을 공유하며, Chroma collection의 distance metric은 `L2`로 고정했다.

Fixture는 임시 persist directory에서 183개 description의 index를 새로 만들고 검색한 뒤, 첫 프로세스를 종료한다. 이후 별도 프로세스가 같은 저장 index를 다시 열어 동일 query와 profile을 검색한다. 이 구조는 같은 in-memory object를 반복 호출한 결과가 아니라 실제 index 재로드 뒤의 결과를 비교한다.

### 3. 대표 자연어 subgoal 결과

영어 세 개와 한국어 한 개의 대표 query를 사용했다. fresh index와 reloaded index에서 결과가 같았으므로 아래에는 top-1과 fresh index의 score를 요약한다. 각 query의 top-10 전체 후보와 score는 실행 로그에 저장했다.

| Text-based subgoal/query context | 기대 skill | top-1 결과 | L2 score |
|---|---|---|---:|
| `Craft a wooden pickaxe.` | `craftWoodenPickaxe` | `craftWoodenPickaxe` | 16.1350 |
| `Mine diamond ore using an iron pickaxe.` | `mineDiamond` | `mineDiamond` | 11.6207 |
| `Breed two cows using wheat.` | `breedCow` | `breedCow` | 25.7432 |
| `밀을 사용해서 소 두 마리를 번식시킨다.` | `breedCow` | `breedCow` | 16.0217 |

L2 score는 확률이나 정확도가 아니라 query와 description vector 사이의 거리다. 같은 profile에서는 값이 작을수록 semantic closeness가 높다.

### 4. Profile과 index reload 결과

| 검사 | Fresh index | Reloaded index | 판정 |
|---|---:|---:|---|
| corpus/index 수 | 183 | 183 | 통과 |
| top-5 known-query recall@5 | 4/4 | 4/4 | 통과 |
| top-10 known-query recall@10 | 4/4 | 4/4 | 통과 |
| top-5가 top-10의 1~5위와 일치 | 4/4 | 4/4 | 통과 |
| fresh/reload candidate 순서 | 비교 기준 | 두 profile·네 query 전부 동일 | 통과 |
| fresh/reload 최대 score 차이 | 비교 기준 | `0.0` | 통과 |

따라서 고정한 encoder·183개 corpus·L2 조건에서 기본 top-5와 별도 top-10 retrieval이 모두 가능하며, index를 재생성하고 저장본을 다시 연 뒤에도 후보 순서와 score가 유지된다고 보고할 수 있다. 이는 네 known query에 대한 retrieval contract 회귀이며 전체 183개 skill의 일반적인 검색 정확도나 Actor 선택 성공률을 의미하지 않는다.

### 5. 관찰된 경고와 남은 작업

이번 경고는 현재 semantic retrieval 결과가 틀렸다는 뜻은 아니다. 다만 지금 사용한 library 연결부가 향후 update나 새 설치 환경에서 같은 기능을 계속 제공한다는 보장이 약하다는 신호이므로, 구형 dependency issue로부터 안전한 연구 기반을 만들기 위해 정리해야 한다.

| 용어·경고 | 간략한 의미 | 위험한 이유 |
|---|---|---|
| `wrapper` | Odyssey 코드가 Sentence Transformer나 Chroma의 내부 API를 직접 다루지 않도록 LangChain이 중간에서 공통 interface로 감싼 adapter다. | wrapper가 바뀌면 model과 DB 자체가 정상이어도 import 경로, 설정 전달 또는 반환 score 형식이 달라져 retrieval 고리가 끊길 수 있다. |
| `deprecation` | 현재는 동작하지만 해당 class·import 경로를 앞으로 제거할 예정이라는 유지보수 경고다. | 지금 무시해도 즉시 실패하지 않지만, 이후 LangChain upgrade에서 `HuggingFaceEmbeddings`나 `Chroma` class가 삭제되면 clean install 또는 실행이 중단될 수 있다. |
| `langchain-huggingface` | Hugging Face embedding wrapper를 LangChain 본체에서 분리해 관리하는 새 공식 package다. | 기존 wrapper와 model option·version 호환성이 완전히 같다고 가정하고 교체하면 vector scale이나 전처리가 달라져 candidate score·순위가 조용히 바뀔 수 있다. |
| `langchain-chroma` | Chroma vector DB 연결 wrapper를 별도 package로 옮긴 새 공식 package다. | Chroma client의 저장 방식, collection 설정이나 score 반환 계약이 달라지면 기존 index를 열지 못하거나 재로드 뒤 후보 순서가 바뀔 수 있다. |
| `telemetry` | Chroma가 client 시작이나 collection 추가 같은 사용 event를 수집·전송하려는 진단 기능이며 skill description이나 embedding 계산 자체는 아니다. | 연구 기능에는 불필요한 외부 동작이고, 실패 메시지가 반복되면 실제 DB 오류를 로그에서 가리거나 제한된 network 환경에서 불필요한 실패 원인이 될 수 있다. |
| `capture() signature` 불일치 | telemetry event를 보내는 쪽과 받는 함수가 기대하는 인자 개수가 다르다는 뜻으로, 관련 package version 조합이 맞지 않음을 보여준다. | 현재는 telemetry만 실패했지만 같은 dependency 조합의 다른 API에서도 호환성 문제가 잠복했을 가능성이 있으며, warning을 error로 처리하는 환경에서는 실행을 막을 수 있다. |
| `clean environment`와 `exact lock` | 기존 cache나 우연히 설치된 package 없이 새 환경을 만들고, 검증한 package의 정확한 version 조합만 다시 설치하는 절차다. | 현재 `.venv`에만 존재하는 간접 dependency 덕분에 우연히 통과한 경우 다른 PC나 재설치에서 재현되지 않는다. version을 고정하지 않으면 같은 명령도 설치 시점에 따라 다른 결과를 낼 수 있다. |

이번 실행에서는 위 경고가 index 생성·persist·reload와 검색을 중단시키지 않았고, fresh/reload 후보 순서와 score도 일치했다. 따라서 현재 retrieval fixture는 통과로 유지하되 dependency 안전성은 완료로 올리지 않는다.

다음 dependency 정비에서는 `langchain-huggingface`와 `langchain-chroma`의 지원 version 조합을 별도 환경에서 검토하고, encoder vector contract와 이번 retrieval fixture를 모두 통과한 조합만 lock한다. telemetry는 끄거나 호환되는 version으로 맞추되, 경고를 숨기는 것만으로 해결했다고 판정하지 않는다. 별도 clean environment의 exact lock 설치와 재실행은 아직 완료하지 않았다.

### 6. 재현 명령과 근거 파일

```bash
cd ~/Documents/MineSkynet
Odyssey/.venv/bin/python Odyssey/scripts/semantic_retrieval_fixture.py
```

- [Retrieval profile fixture](../../Odyssey/scripts/semantic_retrieval_fixture.py)
- [Top-5·top-10 후보와 reload 실행 로그](../log/semantic_retrieval_profiles_2026-08-27.json)
- [Semantic encoder·retrieval manifest](../manifest/odyssey_semantic_encoder.json)
- [공통 retrieval profile 설정](../../Odyssey/odyssey/retrieval_embedding.py)
- [현대화 마일스톤](milestone_goal/modernization_milestone.md)
- [논문–코드–dependency 대응표](paper_code_dependency_map.md)
