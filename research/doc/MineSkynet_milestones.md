# MineSkynet 연구 마일스톤

최종 갱신: 2026-08-06
용도: 구현·실험 진행 상황, 성공 기준, 장애 요인 및 다음 작업 관리  
연구 설계와 근거는 `MineSkynet_blueprint.md`를 기준으로 한다.

## 현재 개발 원칙

- 목표는 과거 실행환경의 bit-exact 복제가 아니라 **현재 작동하는 기능적 Odyssey baseline** 구축이다.
- 반드시 유지할 것은 cloud/controller의 candidate skill 제한 → edge actor의 단일 skill 선택 → Mineflayer 실행 → 성공 판정의 핵심 동작이다.
- edge actor는 짧은 현재 관측과 단일 subgoal만 처리하는 stateless executor로 두며, 장기 이력 기반 in-context 학습·자기반성·새 skill 생성은 기대하지 않는다.
- 실패 이력의 축적, task 재분해, candidate skill 재구성과 in-context 재계획은 cloud planner/reflector와 State Manager의 책임이다.
- Minecraft·Fabric·Python·Node의 구버전은 연구 기여가 아니므로 필요하면 업데이트하되 버전과 변경 이유를 기록한다.
- 의존성 최신화는 한 계층씩 적용하고 매 단계에서 동일 atomic task로 회귀 검증한다.
- 원본 보존 상태와 현대화 실험을 Git branch로 분리한다.
- MineSkynet의 차별점은 원본 환경 복제가 아니라 이기종 edge-cloud routing과 자체 통합 benchmark에 둔다.

## 현재 단기 우선순위: Gemma 3 1B LoRA actor 학습

의존성 현대화가 순서상 선행 작업이지만, 이번 주에는 학습 파이프라인 이해와 local actor 가능성의 조기 확인을 위해 LoRA 트랙을 먼저 진행한다. 이 변경은 현대화를 취소하는 것이 아니라 잠시 보류하는 것이다. LoRA 결과는 Minecraft 런타임 문제와 분리해 먼저 offline으로 평가하고, 실제 Mineflayer 성공률 평가는 runtime blocker 해결 후 수행한다.

학습 원칙은 다음과 같다.

- RTX 3090에서 Gemma 3 1B Instruct 계열을 BF16 기반 LoRA로 학습한다.
- 첫 smoke run에서는 양자화 학습을 사용하지 않는다. INT4는 adapter 병합 여부를 결정한 뒤 배포·추론 단계에서만 비교한다.
- actor 역할만 학습하고 고수준 계획·분해·실패 반성은 cloud planner/reflector에 남긴다.
- actor 입력은 현재 observation·단일 subgoal·제한된 candidate skills의 고정 schema로 압축한다. 장기 trajectory나 9k context를 actor에 제공해 in-context 적응시키는 방향은 이번 범위에서 제외한다.
- base 모델과 LoRA 모델을 동일한 고정 평가셋·prompt·생성 조건으로 비교한다.
- Odyssey·LLM Backend 환경과 섞지 않고 파인튜닝 전용 Conda 환경을 사용한다.

### 현재 정확히 멈춘 지점

- raw `mineWoodLog`는 실제 `oak_log` 인벤토리 증가까지 통과했다.
- raw `craftCraftingTable` smoke script는 나무 채굴과 아이템 회수 후 `Crafting 4 oak_planks...`까지 진입했다.
- 이후 Mineflayer 4.8.1의 `bot.craft`가 Minecraft 1.19.4용 `window_click` packet을 직렬화하는 과정에서 빈 slot을 `undefined`로 전달해 `TypeError: SizeOf error for undefined: Cannot read properties of undefined (reading present)`가 발생했다.
- 이 오류 뒤 bot이 timeout으로 끊겨 판자·작업대 인벤토리 성공 판정을 받지 못했다. 따라서 raw 제작대 테스트는 미완료다.
- MineMA actor의 실제 `mineWoodLog` 선택·실행과 제작대 end-to-end도 아직 미완료다. 나무 subgoal 성공 판정 추가도 남아 있다.
- 의존성 현대화는 이 제작 packet 호환 문제를 포함해 해결할 장기 경로지만, LoRA offline 실험이 끝날 때까지 의도적으로 보류한다.

### 데이터 전처리 현황: 2026-08-06

- [x] Hugging Face 원본 `Aiwensile2/Minecraft_QA-pairs_Instruction_Dataset` 390,317행 다운로드 및 SHA-256 기록
- [x] 구조 오류·빈 텍스트·명백한 placeholder 815행 제거
- [x] 공백·대소문자를 정규화한 exact 중복 10,131행 제거
- [x] 동일 질문의 복수 답변을 보존한 clean corpus 379,371행 생성
- [x] 동일 질문이 서로 다른 split에 섞이지 않도록 SHA-256 기반 train/validation/test 분리
- [x] train 341,282행, validation 19,109행, test 18,980행 및 128행 smoke JSONL 저장
- [x] 저장 결과 재로딩, schema·결측·중복·행 수·split leakage 검증 통과

실행 가능한 전처리 기준본은 `research/mineskynet_finetuning/preprocessing.ipynb`, 수동 학습용 초안은 `preprocessing_revisit.ipynb`에 보존한다. 생성 데이터와 보고서는 `research/mineskynet_finetuning/data/` 아래에 두고 Git에서는 제외한다. 현재 결과는 **Minecraft QA corpus의 보수적 구조 정제본**이며, actor의 observation·goal·candidate skill → action 형식 데이터는 아니다. 표 조각, prompt/answer 역전, 사실 오류 같은 의미적 노이즈는 별도 샘플 감사 또는 규칙 설계가 필요하다.

### Gemma 3 1B BF16 LoRA 프로필 결과: 2026-08-06

RTX 3090에서 `memorize_128`, `pilot_1k`, `generalize_10k`를 실행했고 모든 profile에서 BF16 학습, finite loss 감소, adapter 저장, 새 base model에 adapter 재로드 및 단일 추론까지 통과했다. 각 실행의 config, trainer state, summary와 inference comparison은 `research/mineskynet_finetuning/outputs/gemma3_1b_lora_<profile>/`에 저장했다.

| profile | train rows | optimizer steps | LoRA rank | train loss | peak VRAM | runtime | 제작대 판자 probe |
|---|---:|---:|---:|---:|---:|---:|---|
| `memorize_128` | 128 | 200 | 8 | 0.638 | 3.928 GiB | 171 s | `4`, 정답 |
| `pilot_1k` | 1,000 | 189 | 16 | 2.030 | 4.141 GiB | 138 s | `4`, 정답 |
| `generalize_10k` | 10,000 | 1,250 | 16 | 1.767 | 4.232 GiB | 865 s | `6`, 오답 |

- [x] `memorize_128`의 마지막 loss window가 0.0013까지 감소해 LoRA가 소규모 데이터를 암기할 수 있음을 확인
- [x] 1k·10k subset에서도 학습과 adapter 재로드 파이프라인 검증
- [x] Gemma의 `<eos>`·`<end_of_turn>` 복수 종료 토큰을 보존해 기존 반복 문자열 생성 오류 제거
- [~] base는 제작대 probe에 항상 `6`으로 오답; adapter는 128·1k에서 `4`, 10k에서 `6`으로 규모 증가에 따른 단조로운 품질 개선이 없음
- [!] 단일 QA probe와 token accuracy만으로 actor 성능 또는 Gemma 1B의 Go/No-Go를 판정할 수 없음

현재 결론은 **학습 파이프라인 성공, QA 데이터 규모 효과 미입증, actor 가능성 미검증**이다. 128 profile은 train과 eval이 같아 일반화 근거가 아니며, 10k에서 오답이 유지된 원인이 데이터 관련성·의미적 노이즈·Gemma 1B 용량 중 무엇인지는 아직 분리되지 않았다. QA corpus의 크기만 더 늘리는 작업은 일단 중단하고, 다음 우선순위는 `observation + subgoal + candidate skills → structured action` actor schema와 고정 평가셋을 만드는 것이다.

후속 진단 후보로 **의도적 과적합 및 double descent 실험**을 보류 목록에 둔다. actor용 독립 train/validation/test를 만든 뒤에도 local actor의 학습 용량·추론 일반화 병목이 확인될 경우, 장기 학습에 따른 epoch-wise double descent와 LoRA rank sweep에 따른 capacity-wise 변화를 검토한다. train과 eval이 같은 `memorize_128` 결과만으로는 double descent를 주장하지 않는다.

### LoRA 트랙 완료 기준

1. MineMA fine-tuning 패키지에 포함된 데이터·다운로드 스크립트·참조 출처·라이선스를 확인한다.
2. actor 학습 입력과 정답 schema를 확정하고 train/validation/test를 분리한다.
3. 32~128개 샘플로 과적합 smoke test를 수행해 loss 감소를 확인한다.
4. LoRA adapter 저장·재로드 후 같은 입력에서 추론이 재현되는지 확인한다.
5. base Gemma와 LoRA Gemma의 JSON 유효률, 존재하는 skill 선택률, 정답 skill 정확도를 비교한다.
6. peak VRAM, 학습 시간, sequence length, LoRA rank·alpha·target module을 기록한다.
7. 학습 완료 모델을 INT4로 배포해 단일 actor 추론과 메모리 사용량을 확인한다.

## 보류 중인 런타임 전략: legacy baseline 완료 후 계층별 현대화

현재 환경에 임시 호환 패치를 계속 분산 추가하면 특정 구버전 조합에 더 강하게 결합되는 `dependency stitches`가 생길 수 있다. 반대로 baseline 검증 전에 모든 의존성을 동시에 갱신하면 회귀 원인을 분리할 수 없다. 따라서 다음 두 단계를 명확히 분리한다.

### 단계 A. 최소 방어코드로 legacy baseline 완료

- [x] Mineflayer `/start`의 중앙 진입점 한 곳에서 chunk 준비 완료 전 물리 실행을 보류
- [x] position·velocity의 `NaN`/무한대 감지와 명확한 진단 로그 추가
- [x] workaround를 skill별로 분산하거나 `node_modules`를 직접 수정하지 않음
- [x] raw `mineWoodLog` 나무 채굴 회귀 테스트
- [ ] raw `craftCraftingTable` 제작대 제작 테스트
- [ ] MineMA actor가 `mineWoodLog`를 선택하고 실제 나무를 채굴하는 end-to-end 테스트
- [ ] MineMA actor가 `craftCraftingTable`을 선택하고 실제 제작대를 만드는 end-to-end 테스트
- [ ] Minecraft·Mineflayer·MineMA·Odyssey 로그와 사용 버전 보존
- [ ] 성공 상태를 `odyssey-legacy-baseline-1.19.4`와 같은 Git tag로 고정

임시 방어코드는 아래 조건을 만족해야 한다.

- bridge의 한 경계에서만 적용한다.
- 적용 이유, 재현 조건, 제거 조건을 문서화한다.
- 기능을 조용히 우회하지 않고 비정상 좌표를 로그에 남긴다.
- 현대화 후 동일 문제가 재현되지 않으면 제거한다.

### 단계 B. modern runtime으로 계층별 업데이트

`experiment/modern-odyssey` 계열 branch에서 다음 순서로 한 계층씩 갱신한다. 여기서 최신화는 모든 패키지의 무조건적인 최신 버전 설치가 아니라, 서로 공식 지원되는 안정 버전 조합을 선택하는 것을 의미한다.

- [ ] 1단계: Minecraft 1.19.4를 유지한 채 Mineflayer·minecraft-protocol·prismarine-physics 갱신
- [ ] 2단계: pathfinder·tool·collectblock·PVP·Hawkeye plugin 호환 수정
- [ ] 3단계: 지원되는 Node.js LTS 선택, npm lockfile 재생성 및 `npm ci` 검증
- [ ] 4단계: Minecraft·Fabric Loader·Fabric API·server mod·Java를 하나의 호환 묶음으로 갱신
- [ ] 5단계: Odyssey Python·LangChain·Chroma·sentence-transformer 계층 갱신
- [ ] 6단계: MineMA Backend의 PyTorch·Transformers·FastAPI 계층 갱신
- [ ] 임시 legacy workaround의 필요 여부 재검증 및 불필요한 코드 제거
- [ ] `legacy-reproduction`과 `modern-mineskynet` 두 실행 profile 문서화

각 단계가 끝날 때마다 아래 회귀 테스트를 모두 통과해야 다음 계층으로 진행한다.

1. bot 접속 30초 유지 및 모든 좌표 유한값 확인
2. raw 나무 채굴 및 인벤토리 증가
3. raw 제작대 제작 및 인벤토리 증가
4. MineMA actor 나무 채굴
5. MineMA actor 제작대 제작

한 번에 여러 계층을 갱신하지 않는다. 실패한 최초 단계의 dependency diff와 로그를 남긴 뒤 해당 계층에서 원인을 해결한다.

## 과거 작업 기록: 2026-07-30

- [x] 원본의 완전한 버전 복제보다 현재 작동하는 기능적 baseline을 우선하기로 결정
- [x] 최신화 실험용 `experiment/modern-odyssey` branch 생성 및 전환
- [x] Minecraft 컨테이너 이미지 다운로드와 서버 초기 실행 시도
- [x] 서버 실패 원인을 Fabric Loader와 최신 pause 모드의 버전 불일치로 특정
- [x] Fabric Loader만 먼저 업데이트하고 Minecraft 1.19.4 서버 기동 확인
- [x] Minecraft 1.19.4/Fabric 호환을 위해 Docker Java runtime을 17로 고정
- [x] Mineflayer 단독 접속과 observation 반환 확인
- [x] raw `mineWoodLog.js`로 나무 블록 1개 채굴 및 인벤토리 획득
- [ ] MineMA-8B-v3 actor를 연결해 같은 태스크 수행

오늘은 게임 버전과 모든 의존성을 동시에 올리지 않는다. 우선 현재 Minecraft 1.19.4에서 서버와 bot의 기능적 baseline을 만든 뒤 계층별로 최신화한다.

## 상태 표기

- [x] 완료 및 검증
- [ ] 미완료
- [~] 진행 중 또는 부분 완료
- [!] 차단되었거나 결정 필요

## 0806 목표: LoRA-first actor 검증

이번 주에는 runtime 현대화보다 Gemma 3 1B LoRA 학습 파이프라인을 먼저 완성한다. Minecraft online 성공 여부와 모델의 offline actor 성능을 분리해 기록한다. local actor는 실행 중 경험을 누적해 스스로 skill을 개선하는 주체가 아니라, 사전에 학습된 고정 policy로 제한된 candidate 중 하나를 선택하는 모듈로 평가한다.

### 1. 데이터와 학습 대상 감사

- [x] `MineMA-Model-Fine-Tuning` 저장소에는 raw data가 직접 포함되지 않고 다운로드 대상만 제시됨을 확인
- [x] Hugging Face 다운로드 위치와 접근 조건 확인 및 raw data 다운로드
- [x] 데이터 출처, revision, SHA-256, CC BY-NC-SA 3.0 라이선스 기록
- [x] 원본 `instruction`·`input`·`output` schema와 빈 `input` 구조 확인
- [ ] MineSkynet actor에 필요한 입력을 observation·goal·candidate skills로 정의
- [ ] 정답을 skill 이름 또는 실행 action schema로 고정
- [~] QA corpus는 normalized instruction 단위로 train/validation/test 누수를 방지함; actor 데이터는 schema 확정 후 task instance/template 그룹 단위로 분리
- [x] QA baseline용 고정 test 18,980행을 학습 전에 저장

### 2. RTX 3090 LoRA 환경과 smoke training

- [x] 전처리 전용 독립 venv와 Jupyter kernel 구성; Odyssey와 LLM Backend 패키지에 영향 없음
- [x] 학습 전용 path-based Conda 환경에 PyTorch 2.12.1+cu130 및 Transformers·TRL·PEFT 설치
- [~] Gemma 3 1B Instruct base model과 tokenizer 로컬 저장; 정확한 Hub revision hash 기록은 남음
- [x] RTX 3090 CUDA·BF16·gradient checkpointing 동작 확인
- [x] LoRA target module, rank, alpha, dropout을 실행 profile로 분리
- [x] sequence length 512에서 128개 과적합 시험
- [x] 128·1k·10k 모두 train loss 감소, NaN·OOM 없음
- [x] profile별 adapter checkpoint 저장·재로드·단일 추론 확인
- [x] seed, package version, peak VRAM과 소요 시간을 output에 기록

### 3. 통제된 학습과 offline 평가

- [~] 학습 전 base Gemma의 제작대 단일 probe 저장; actor용 고정 test set은 미작성
- [~] 128·1k·10k subset LoRA 실행; 전체 341k train은 실행하지 않음
- [x] profile별 validation loss 기록 및 `memorize_128` 의도적 과적합 확인
- [ ] JSON 유효률 측정
- [ ] candidate에 존재하는 skill 선택률 측정
- [ ] 정답 skill top-1 정확도와 task별 confusion 기록
- [~] base와 LoRA를 동일 제작대 prompt·greedy decoding으로 비교; 단일 QA probe라 actor 성능 근거는 아님
- [ ] actor schema를 512~1k 이하의 짧은 token budget으로 고정하고 지연·VRAM 측정
- [~] 제작대 성공·실패 예시 저장; 데이터 문제와 모델 용량의 원인 분리는 남음

### 4. 배포 검증과 runtime 복귀 조건

- [x] BF16 base와 profile별 LoRA adapter 조합의 offline 단일 추론 확인
- [ ] 배포용 INT4 모델 또는 adapter 조합 생성
- [ ] INT4의 출력 정확도·지연·peak VRAM을 BF16 결과와 비교
- [ ] Odyssey actor adapter가 요구하는 endpoint 계약 초안 작성
- [ ] raw crafting blocker 해결 전에는 Minecraft 성공률을 LoRA 성능으로 주장하지 않음
- [ ] offline 기준을 통과하면 의존성 현대화 또는 최소 crafting fix로 복귀

이번 주 최소 성공 기준:

> Gemma 3 1B의 BF16 LoRA smoke training에서 loss 감소를 확인하고, 저장한 adapter를 다시 로드해 actor 형식의 응답을 생성하며, 동일한 고정 test set에서 base 모델과 비교 가능한 결과표를 남긴다.

### 이번 주 보류 항목

- [!] raw 작업대 제작: `window_click`의 undefined slot 직렬화 오류에서 중단
- [!] MineMA actor Minecraft end-to-end: skill 선택과 subgoal 성공 판정 미완료
- [~] 의존성 현대화: LoRA offline 결과 확보 후 재개
- [ ] Gemma LoRA의 Minecraft online 평가: runtime blocker 해결 후 수행

## 전체 연구 마일스톤

현재 실행 순서는 예외적으로 M1의 LoRA offline 검증 일부를 먼저 수행한 뒤 M0의 online baseline과 M0.5 현대화로 복귀한다. 번호는 연구 의존관계를 나타내므로 바꾸지 않는다.

### M0. 기능적 Odyssey baseline 구축

- [~] Odyssey 개발환경 구성
- [x] 현대화 실험 branch `experiment/modern-odyssey` 분리
- [x] Minecraft 1.19.4·Fabric Loader 0.15.11·Java 17 서버 조합 고정 및 Mineflayer 접속 검증
- [x] 모델을 제외한 raw `mineWoodLog` 행동 계층 검증
- [x] Mineflayer 재접속 시 chunk/물리 준비 순서를 보장하는 중앙 방어코드 적용
- [ ] MineMA-8B-v3 단일 actor 재현
- [~] 나무 채굴 atomic task 성공: raw skill 완료, MineMA actor end-to-end 대기
- [ ] raw 작업대 제작 및 MineMA 작업대 제작 subgoal 성공
- [ ] 재현 절차와 원본 대비 호환성 수정 목록 확정
- [ ] legacy baseline commit/tag 고정

완료 조건: 현재 환경에서 Odyssey의 핵심 동작을 반복 실행할 수 있고, 사용 버전·호환성 수정·로그가 보존된다.

### M0.5. 의존성 현대화와 dual runtime 확립

- [ ] legacy baseline과 분리된 modern runtime branch 확인
- [ ] Node/Mineflayer 계층 현대화 및 atomic task 회귀 검증
- [ ] Minecraft/Fabric/mod/Java 호환 묶음 현대화 및 회귀 검증
- [ ] Odyssey Python retrieval 계층 현대화 및 회귀 검증
- [ ] MineMA Backend 추론 계층 현대화 및 회귀 검증
- [ ] legacy 전용 workaround 제거 가능성 검토
- [ ] `legacy-reproduction`과 `modern-mineskynet`의 버전 matrix 및 실행법 작성

완료 조건: 원본 비교용 legacy profile과 실제 MineSkynet 실험용 modern profile이 모두 재현 가능하며, 동일 atomic test suite 결과로 현대화에 따른 동작 변화를 설명할 수 있다.

### M1. Local actor 교체 가능성 검증

- [ ] 장기 이력·자기반성·skill 생성을 제외한 stateless short-context actor 계약 정의
- [ ] 공통 actor endpoint와 학습 sample schema 정의
- [x] Gemma 3 1B base 제작대 zero-shot 결과 저장: `6`으로 오답
- [x] MineMA 학습 데이터의 위치·출처·라이선스 감사 및 QA 구조 전처리
- [x] 소규모 BF16 LoRA 과적합 smoke test
- [~] 128·1k·10k LoRA와 adapter 저장·재로드 검증; 전체 corpus 학습은 보류
- [ ] base Gemma와 LoRA Gemma의 offline actor 정확도 비교
- [ ] INT4 배포본의 정확도·지연·메모리 비교
- [ ] 출력 파서와 제한된 재시도 정책 정의
- [ ] runtime blocker 해결 후 atomic Minecraft task suite 평가
- [ ] MineMA와 Gemma의 성공률·지연·메모리 비교
- [ ] Gemma actor의 Go/No-Go 판정

완료 조건: actor 모델만 교체한 통제 실험 결과가 있고, offline 개선과 Minecraft online 성공을 구분해 보고할 수 있다. actor의 성공은 고정된 짧은 입력에서의 skill 선택·실행으로 판정하며 in-context adaptation을 요구하지 않는다.

### M2. 세 물리 노드 연결

- [ ] Raspberry Pi 4B 4GB OS·RAM·온도·전력 측정 환경 구성
- [ ] GTX 1050 Ti 장비의 CPU·RAM·VRAM·OS 확인
- [ ] RTX 3090, GTX 1050 Ti, Raspberry Pi Tailscale 연결 검증
- [ ] 각 노드에 Mineflayer executor 또는 제어 API 배치
- [ ] Minecraft 서버에 bot 3개 동시 접속
- [ ] 노드별 로그와 시간 동기화

완료 조건: 세 물리 장치가 각각 독립된 bot avatar를 안정적으로 제어한다.

### M3. Atomic capability calibration

- [ ] 공통 atomic task 목록과 난이도 정의
- [ ] 장치·모델 조합별 성공률 측정
- [ ] 평균·P95 완료 시간 측정
- [ ] 에너지와 peak memory 측정
- [ ] 통신량과 재시도 횟수 측정
- [ ] agent capability profile 생성

완료 조건: scheduler가 사용할 `P(success)`, latency, energy, retry profile이 생성된다.

### M4. Cloud planner와 State Manager

- [ ] 구조화 subtask schema 정의
- [ ] dependency DAG 표현 정의
- [ ] 공통 agent 상태와 capability schema 정의
- [ ] inventory·위치·진행 상태 동기화
- [ ] skill retrieval과 candidate filtering을 cloud/controller 계층에 배치
- [ ] task history·실패 trace를 State Manager에 저장하고 planner/reflector의 in-context 재계획에 사용
- [ ] cloud planner의 분해·배정·재계획 구현
- [ ] API 호출 비용과 토큰 사용량 기록

완료 조건: cloud planner가 여러 local executor에 작업을 배정하고 실패를 재계획한다.

### M5. Capability-aware allocation

- [ ] static capability-aware scheduler 구현
- [ ] uniform·random·fixed-role baseline 구현
- [ ] cloud-only와 edge-only baseline 구현
- [ ] 이동·handoff·동기화 비용 반영
- [ ] 실패·timeout 시 재할당 구현
- [ ] allocation decision trace 저장

완료 조건: 동일 task graph를 여러 배정 정책으로 반복 비교할 수 있다.

### M6. 통합 벤치마크

- [ ] cooperative Minecraft task suite 확정
- [ ] 성공률·makespan·API 비용 측정
- [ ] local latency·energy·통신량 측정
- [ ] synchronization·retry·orchestration overhead 분해
- [ ] 네트워크 지연·손실·노드 실패 조건 실험
- [ ] 반복 횟수와 통계 분석 방법 확정
- [ ] 결과 표·그래프와 원시 로그 생성

완료 조건: 제안 방식과 모든 baseline의 재현 가능한 비교 결과가 존재한다.

### M7. 논문·공개 패키지 정리

- [ ] 핵심 주장과 실험 결과 연결
- [ ] 관련 연구와 차별성 재검토
- [ ] 설치 및 재현 README 작성
- [ ] 하드웨어·모델·양자화 설정 공개
- [ ] benchmark task와 metric 정의 공개
- [ ] 알려진 한계와 실패 사례 정리
- [ ] 코드·설정·로그 공개 범위 검토

## 실험 기록 템플릿

각 실험은 아래 형식으로 누적한다.

```text
실험 ID:
날짜/commit:
목적:
하드웨어:
모델/revision/양자화:
Minecraft world seed 및 초기 상태:
태스크:
비교 조건:
반복 횟수:
성공 횟수:
완료 시간 평균/P95:
peak RAM/VRAM:
에너지:
API token/비용:
네트워크 송수신량:
retry/replan 횟수:
로그 경로:
결론:
다음 조치:
```

## 현재 장애 요인 및 주의사항

- [!] raw 제작대 제작은 `bot.craft`의 1.19.4 `window_click` packet 직렬화 오류에서 중단됐다. 아이템 회수와 판자 제작 진입까지는 확인했지만 `crafting_table` 인벤토리 증가는 아직 검증하지 못했다.
- [!] 이 runtime blocker가 남아 있으므로 LoRA 학습 결과는 먼저 offline actor 선택 성능으로만 평가하며 Minecraft 실행 성공으로 해석하지 않는다.

- MineMA-8B-v3와 임베딩 모델 다운로드 및 단일 추론·embedding 검증은 완료됐다.
- LLM Backend는 Odyssey와 별도의 Python 환경으로 격리해야 한다.
- LLM Backend 전용 환경은 `LLM-Backend/.venv`이며 Python 3.10.20, PyTorch 2.2.0+cu121, Transformers 4.43.3으로 고정했다.
- LLM Backend 환경에서 RTX 3090, CUDA, BF16 지원과 포트 9999의 `/ping` 응답을 검증했다.
- Odyssey의 기본 subgoal 판정에는 `mine one wood log`가 없으므로 최소 판정 추가가 필요하다.
- `Server Pause 1.3.1`과 `iChunUtil 1.0.2` 요구사항에 맞춰 Fabric Loader를 0.15.11로 업데이트했다.
- `itzg/minecraft-server:latest`가 Java 25를 사용해 구 Mixin이 class-file version 69를 처리하지 못했다. Minecraft 1.19.4 서버는 `itzg/minecraft-server:java17`로 고정한다.
- 서버 로그의 runner `Done`은 성공 표시가 아니다. Minecraft의 `Done (...)! For help, type "help"`와 컨테이너의 지속적인 `Up` 상태를 함께 확인한다.
- 원본 Node 의존성의 넓은 버전 범위가 최신 패키지를 설치해 빌드 오류를 일으켜 Mineflayer 계열을 호환 버전으로 고정했다.
- Mineflayer는 baseline 동안 Node.js 20.13.1로 고정하지만, `Invalid move player packet received`는 Node 20에서도 재현됐으므로 Node 버전만의 문제로 간주하지 않는다.
- 재현 결과 저장 위치 `(424.5, 75, -41.5)`에서 접속한 `bot`의 첫 물리 계산 후 x·z 좌표가 `NaN`으로 변했고, 해당 position packet을 서버가 거부했다. 월드 스폰으로 재설정한 뒤 순정 Mineflayer bot은 안정적으로 유지됐다.
- 현재 우선 가설은 낮은 view distance에서 저장 위치의 chunk가 준비되기 전에 구버전 `prismarine-physics`가 시작되는 문제다. 중앙 chunk-readiness/finite-coordinate guard로 baseline을 완료한 후 modern branch에서 라이브러리 갱신으로 제거 가능성을 검증한다.
- 중앙 guard 적용 후 soft reset, hard reset+position 복원, 30초 이상 접속 유지와 raw `mineWoodLog` 회귀 테스트를 통과했다. 첫 회귀 시도는 Creeper 사망으로 timeout됐고, peaceful·낮 조건에서 재실행해 `oak_log: 1`을 확인했다.
- Raspberry Pi에서는 Minecraft 서버가 아니라 headless Mineflayer executor와 경량 추론만 실행한다.

## 실행 명령 모음

### A. 검증된 raw baseline 재실행

터미널 3개를 동시에 사용한다. 실행 순서는 Minecraft → Mineflayer → bot 접속 → smoke test이다.

#### 터미널 1: Minecraft 서버 및 로그

```bash
cd ~/Documents/MineSkynet
cd Odyssey
docker compose up -d
docker compose ps
docker compose logs -f mc
```

로그 화면은 `Ctrl+C`로 종료해도 컨테이너가 계속 실행된다. 서버까지 중지하려면 다음을 실행한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
docker compose stop mc
```

#### 터미널 2: Mineflayer bridge

```bash
cd ~/Documents/MineSkynet
cd Odyssey/odyssey/env/mineflayer
nvm use 20.13.1
node --version
node index.js 3000
```

`node --version`이 `v20.13.1`인지 확인하고 이 터미널은 계속 열어 둔다.

#### 터미널 3: bot 접속 요청

```bash
curl -X POST http://127.0.0.1:3000/start \
  -H 'Content-Type: application/json' \
  -d '{
    "host": "127.0.0.1",
    "port": 25565,
    "username": "bot",
    "waitTicks": 20,
    "reset": "soft"
  }'
```

응답과 Minecraft 로그의 `bot joined the game`을 확인한 뒤, 같은 터미널에서 raw 나무 채굴 테스트를 실행한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
conda activate ./.venv
python scripts/smoke_test_mine_wood.py
```

성공 조건은 `inventory`의 `*_log` 수량 증가와 `PASS: mineWoodLog collected at least one wood log` 출력이다.

### B. MineMA 다운로드 확인 및 재개

다운로드 용량을 1초 간격으로 확인한다.

```bash
cd ~/Documents/MineSkynet
watch -n 1 'du -sh ./LLM-Backend/models/MineMA-8B'
```

다운로드 프로세스가 중단됐을 때만 아래 명령으로 이어받는다. 여러 터미널에서 동시에 실행하지 않는다.

```bash
cd ~/Documents/MineSkynet
cd LLM-Backend
conda activate ./.venv
HF_HOME=./.cache/huggingface \
HF_HUB_DISABLE_XET=1 \
hf download Aiwensile2/MineMA-8B \
  --revision 126a11c79009fa7ea19aed2aa3a959f0929afbb2 \
  --include 'MineMA-3-8b-v3/*' \
  --local-dir ./models/MineMA-8B \
  --max-workers 4
```

완료 체크포인트 경로는 `LLM-Backend/models/MineMA-8B/MineMA-3-8b-v3`이다.

### C. LLM Backend 실행 및 확인

MineMA 다운로드, `conf/config.json` 모델 경로 등록, `/ping`과 `llama3_8b_v3` 단일 추론까지 검증됐다.

#### 터미널 4: LLM Backend

```bash
cd ~/Documents/MineSkynet
cd LLM-Backend
conda activate ./.venv
HF_HOME=./.cache/huggingface python main.py
```

#### 터미널 5: Backend 상태 확인

```bash
curl --fail http://127.0.0.1:9999/ping
nvidia-smi
```

`/ping` 성공 응답은 `{"data":"pong!"}`이다. MineMA 단일 추론과 Odyssey wrapper 연결도 완료됐으며, 다음 검증 대상은 실제 actor skill 선택이다.

## 다음 작업

1. `MineMA-Model-Fine-Tuning`의 데이터·학습 코드·문서와 외부 다운로드 출처를 감사한다.
2. Gemma 3 1B actor용 학습 schema와 고정 offline test set을 확정한다.
3. 파인튜닝 전용 Conda 환경을 만들고 base 모델의 zero-shot 결과를 저장한다.
4. 32~128개 샘플 BF16 LoRA 과적합 smoke test를 실행한다.
5. adapter 저장·재로드와 base 대비 offline 평가를 완료한다.
6. INT4 배포 추론을 확인한 뒤 raw crafting blocker와 의존성 현대화로 복귀한다.
