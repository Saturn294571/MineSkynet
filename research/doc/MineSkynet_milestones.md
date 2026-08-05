# MineSkynet 연구 마일스톤

최종 갱신: 2026-07-31  
용도: 구현·실험 진행 상황, 성공 기준, 장애 요인 및 다음 작업 관리  
연구 설계와 근거는 `MineSkynet_blueprint.md`를 기준으로 한다.

## 현재 개발 원칙

- 목표는 과거 실행환경의 bit-exact 복제가 아니라 **현재 작동하는 기능적 Odyssey baseline** 구축이다.
- 반드시 유지할 것은 관측 → skill retrieval/선택 → Mineflayer 실행 → 성공 판정의 핵심 동작이다.
- Minecraft·Fabric·Python·Node의 구버전은 연구 기여가 아니므로 필요하면 업데이트하되 버전과 변경 이유를 기록한다.
- 의존성 최신화는 한 계층씩 적용하고 매 단계에서 동일 atomic task로 회귀 검증한다.
- 원본 보존 상태와 현대화 실험을 Git branch로 분리한다.
- MineSkynet의 차별점은 원본 환경 복제가 아니라 이기종 edge-cloud routing과 자체 통합 benchmark에 둔다.

## 현재 실행 전략: legacy baseline 완료 후 계층별 현대화

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

## 오늘 작업: 2026-07-30

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

## 이번 주 목표

### 1. 랩미팅용 연구계획 정리

- [ ] 연구 문제를 `heterogeneous edge-cloud embodied multi-agent orchestration`으로 명확히 표현
- [ ] VillagerAgent 등 기존 다중 Minecraft agent 연구와 차별점 정리
- [ ] 실제 이기종 하드웨어, 양자화 모델, 통신·전력·비용 통합 벤치마크를 핵심 기여로 제시
- [ ] 시스템 구성도와 단계별 실험 계획 정리
- [ ] 랩미팅 피드백 기록 및 블루프린트 반영

담당: 사용자 직접 작성·발표

### 2. RTX 3090에서 기능적 Odyssey baseline 구축

오늘의 필수 성공 기준:

> MineMA actor가 Odyssey skill library에서 `mineWoodLog`를 선택하고, Mineflayer bot이 실제 나무 블록 1개를 채굴하여 인벤토리에 `*_log`가 증가한다.

#### 이미 완료된 준비

- [x] RTX 3090 24GB 및 CUDA 사용 가능 확인
- [x] Docker와 Docker Compose 설치·권한 확인
- [x] Odyssey 전용 Conda Python 3.10 환경 생성
- [x] Odyssey editable install 및 주요 Python import 확인
- [x] Mineflayer 프로젝트 로컬 npm 의존성 설치
- [x] `mineflayer-collectblock` TypeScript 빌드
- [x] Fabric 1.19.4 Docker Compose 구성 작성
- [x] Fabric API와 최신 pause 모드 조합을 Fabric Loader 0.15.11에서 로드
- [x] Odyssey `conf/config.json` 기본 골격 생성

#### 남은 실행 순서

- [x] Minecraft Fabric 서버 이미지 다운로드 및 컨테이너 생성
- [x] Fabric Loader를 최신 pause 모드 요구사항에 맞춰 0.15.11로 업데이트
- [x] Docker image를 `itzg/minecraft-server:java17`로 고정
- [x] 서버 로그에서 Minecraft의 `Done (9.114s)! For help, type "help"` 확인
- [x] Fabric loader와 서버 모드가 오류 없이 로드되는지 확인
    - 서버 실행
        cd ~/Documents/MineSkynet
        cd Odyssey
        docker compose up -d
        docker compose ps
        docker compose logs -f mc
    - 서버 중지
        docker compose stop mc
- [x] Mineflayer 단독 접속 및 observation 반환 확인
  - Node.js 22에서 `Invalid move player packet received`가 발생하여 Odyssey 공식 환경과 동일한 Node.js 20.13.1로 전환
  - 결과:
```text
odyssey-mc  | [23:05:33] [Server thread/INFO]: bot[/172.18.0.1:53686] logged in with entity id 109 at (353.5, 69.0, -103.5)
odyssey-mc  | [23:05:33] [Server thread/INFO]: bot joined the game
```

- [x] raw `mineWoodLog.js` 실행으로 모델 외 환경 검증
  - `mineflayer-collectblock`의 아이템 드롭 감지 반경을 현실적인 범위로 보정
  - `scripts/smoke_test_mine_wood.py`에서 `oak_log` 인벤토리 수량 증가 확인
  - 결과: `PASS: mineWoodLog collected at least one wood log`
- [x] 원본 임베딩 모델 `paraphrase-multilingual-MiniLM-L12-v2` 다운로드 및 384차원 embedding 생성 검증
- [x] LLM Backend 전용 Conda Python 3.10 환경 `LLM-Backend/.venv` 생성
- [x] MineMA-8B-v3 모델 다운로드 및 4개 safetensors shard 검증 (공식 revision `126a11c`, 약 16.1GB)
- [x] LLM Backend의 `llama3_8b_v3` endpoint 기동
- [x] `/ping` 및 MineMA 단일 추론 성공 (`Pickaxe`, VRAM 약 15.8GiB)
- [x] Odyssey 설정에 Minecraft·Node·LLM·embedding endpoint 연결 및 MineMA wrapper 호출 성공
- [ ] 나무 채굴용 최소 성공 판정 추가
- [ ] MineMA actor를 통한 `mineWoodLog` 선택 확인
- [ ] 실제 나무 블록 1개 채굴 및 인벤토리 증가 확인
- [ ] Minecraft, Mineflayer, LLM Backend, Odyssey 로그 보존
- [ ] 재현 명령과 수정 사항 문서화

#### 단계별 판정

| 단계 | 성공 조건 | 실패 시 우선 점검 |
|---|---|---|
| Minecraft | 서버 로그에 `Done`, 25565 접속 가능 | Fabric·모드·볼륨 권한 |
| Mineflayer | `bot` 접속, observation 반환 | Node 버전·Mineflayer·서버 버전 |
| Raw skill | MineMA 없이 나무 1개 채굴 | pathfinder·skill 코드·월드 상태 |
| LLM Backend | `llama3_8b_v3`이 유효 응답 반환 | 모델 revision·VRAM·Transformers |
| Actor | `mineWoodLog` skill 선택 | embedding retrieval·프롬프트·응답 형식 |
| End-to-end | `*_log` 인벤토리 수량 증가 | 위 계층을 역순으로 분리 점검 |

### 3. Gemma 3 1B actor-only 가능성 시험

선행 조건: 원본 MineMA 나무 채굴 baseline 성공

- [ ] MineMA 테스트와 동일한 초기 월드·관측·skill 후보 고정
- [ ] Gemma 3 1B instruct 모델을 파인튜닝 없이 actor endpoint로 연결
- [ ] 모델별 adapter 외 Odyssey 행동 로직은 동일하게 유지
- [ ] 유효 JSON 및 skill 이름 생성률 측정
- [ ] 존재하는 skill 선택률 측정
- [ ] 실제 실행 성공률 측정
- [ ] 나무 블록 채굴 성공률을 최소 5회 반복 측정
- [ ] 응답 지연, peak VRAM/RAM, 생성 토큰 수 기록
- [ ] MineMA baseline과 동일 표로 비교

이번 단계에서는 파인튜닝, planner 교체, critic 교체를 수행하지 않는다.

## 전체 연구 마일스톤

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

- [ ] 공통 actor endpoint 계약 정의
- [ ] Gemma 3 1B zero/few-shot 연결
- [ ] 출력 파서와 제한된 재시도 정책 정의
- [ ] atomic task suite 선정
- [ ] MineMA와 Gemma의 성공률·지연·메모리 비교
- [ ] Gemma actor의 Go/No-Go 판정

완료 조건: actor 모델만 교체한 통제 실험 결과가 존재한다.

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

1. Mineflayer `/start`에 중앙 chunk-readiness 및 finite-coordinate 방어를 추가한다.
2. raw 나무 채굴과 제작대 제작 smoke test를 완료한다.
3. MineMA actor 나무 채굴과 제작대 제작 end-to-end 테스트를 완료한다.
4. legacy baseline의 로그·버전·재현 명령을 보존하고 commit/tag로 고정한다.
5. modern runtime branch에서 계층별 의존성 업데이트와 동일 회귀 테스트를 시작한다.
