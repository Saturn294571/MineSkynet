# 이기종 Edge-Cloud Minecraft Multi-Agent 연구 컨텍스트
- MineSkynet : heterogeneous Edge-Cloud Minecraft Multi-Agent framework (가제)

작성일: 2026-07-18  
최종 갱신: 2026-07-30  
용도: 새 세션 인계 및 연구 방향 고정

## 1. 현재 확정된 연구 방향

### 한 문장 정의

연산 능력이 서로 다른 세 대의 edge computer에서 각각 독립적인 Minecraft bot drone를 실행하고, 중앙 cloud-tier control mothership이 공동 목표의 분해·배정·상태 관리·실패 재계획을 담당하도록 하는 **heterogeneous edge-cloud embodied multi-agent system**을 연구한다.

### 핵심 연구 질문

> 통합 cloud-tier orchestrator가 연산 성능과 local LLM 능력이 서로 다른 Minecraft bot drone들에게 subtask를 적절히 배정하는 구조는 cloud-only, local-only 또는 고정 역할 방식보다 낮은 비용으로 유사하거나 더 높은 협력 task 성공률을 달성할 수 있는가?

### 핵심 가설

1. 복잡한 계획만 cloud-tier mothership에 맡기고 실행은 edge drone가 담당하면 cloud-only 방식보다 API 비용을 줄일 수 있다.
2. agent별 수행 능력을 고려한 task allocation은 agent 차이를 무시한 균등·무작위 배정보다 성공률과 완료 시간을 개선한다.
3. 병렬화 가능한 subtask를 여러 drone에 배정하면 강한 단일 agent보다 전체 task 완료 시간이 감소한다.
4. planning, communication, state synchronization 비용을 모두 포함한 뒤에도 일정 조건에서는 edge-cloud 협력의 이득이 남는다.

## 2. 시스템의 정확한 의미

세 컴퓨터가 하나의 drone 내부 연산을 나누는 구조가 아니다. **각 컴퓨터가 Minecraft 세계에 접속한 별도의 bot avatar 하나를 담당한다.**

```text
                  MineSkynet Cloud-tier Mothership
        ┌──────────────────────────────────────────────┐
        │ Global Orchestrator                          │
        │ goal decomposition / DAG / allocation       │
        │                                              │
        │ Shared State Service                         │
        │ world / inventory / capability / task state │
        │                                              │
        │ Evaluator & Replanner                        │
        │ validation / reflection / retry / reassign  │
        └──────────────────────┬───────────────────────┘
                               │ structured task protocol
                 ┌─────────────┼─────────────┐
                 │             │             │
          Raspberry Pi    GTX 1050 Ti    RTX 3090
            Actor A         Actor B        Actor C
          local model     local model    local model
          + executor      + executor     + executor
                 │             │             │
                 └─── Shared Minecraft World ───┘
```

여기서 `agent`, `bot`, `worker`, `drone`는 한 Minecraft avatar와 그 avatar를 제어하는 local process의 묶음을 뜻한다. 단순 compute worker나 하나의 모델을 분산 추론하는 node를 뜻하지 않는다.

## 3. 보유 자원과 예상 역할

### 확인된 장비

- Raspberry Pi: Raspberry Pi 4B, RAM 4GB
- GTX 1050 Ti 컴퓨터: VRAM과 CPU/RAM은 추후 확인
- RTX 3090 컴퓨터: VRAM 24GB, 현재 주 개발 장비
- 외부 cloud LLM API: 고난도 계획과 재계획에 제한적으로 사용

### 3090 개발·실행 환경

2026-07-19 기준 3090 주 개발 장비에서 다음 환경을 확인했다.

| 항목 | 확인된 상태 |
|---|---|
| GPU | NVIDIA GeForce RTX 3090, VRAM 24GB |
| GPU driver | 595.71.05, host에서 `nvidia-smi` 정상 |
| System RAM | 30GB, swap 8GB |
| Java | OpenJDK 17 |
| Docker | 29.1.3 |
| Docker Compose | 2.40.3 |
| Node.js | Mineflayer 실행은 20.13.1로 고정, system Node는 22.22.1 |
| npm | 9.2.0 |
| Odyssey Python | 저장소 전용 Conda Python 3.10.20 |

#### Conda 격리 원칙

시스템 Python은 3.14이므로 Odyssey에 직접 패키지를 설치하지 않는다. Python 의존성은 다음 저장소 내부 Conda prefix에만 설치한다.

```text
/home/pluto2479/Documents/Odyssey/Odyssey/.venv
```

환경 활성화 명령은 다음과 같다.

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate /home/pluto2479/Documents/Odyssey/Odyssey/.venv
```

긴 prefix 대신 terminal prompt에 `(MineSkynet)`만 표시하도록 해당 환경에서 설정한다.

```bash
conda config --env --set env_prompt '(MineSkynet) '
conda deactivate
conda activate /home/pluto2479/Documents/Odyssey/Odyssey/.venv
```

로그아웃하거나 새 terminal을 열면 Conda 환경은 자동 활성화되지 않는다. 다시 `source`와 `conda activate`를 수행한다. 편의를 위한 shell alias는 선택적으로 사용한다.

```bash
alias mineskynet-env='conda activate /home/pluto2479/Documents/Odyssey/Odyssey/.venv'
```

활성화 검증은 다음 두 명령으로 한다.

```bash
python --version
which python
```

예상 Python 경로는 `/home/pluto2479/Documents/Odyssey/Odyssey/.venv/bin/python`이다.

다음 원칙을 유지한다.

- `sudo pip`, system Python 대상 `pip install`, base Conda 환경 설치를 사용하지 않는다.
- `python3 -m venv`는 현재 system Python 3.14를 사용하므로 Odyssey 환경 생성에 사용하지 않는다.
- `pip freeze > requirements.txt`로 원본 Odyssey 요구사항 파일을 덮어쓰지 않는다.
- Odyssey 재현용 dependency spec과 실제 해결된 lock/constraints 파일을 분리한다.
- Voyager에서 상속된 의존성은 이름만 보고 삭제하지 않고 실제 Odyssey import와 실행 경로를 확인한 뒤 제거·업데이트한다.
- 원본 재현 환경과 이후 MineSkynet 개선 환경의 차이를 문서화한다.

#### Docker 설치와 권한

Minecraft Fabric server는 우선 Docker Compose로 headless 실행한다. 3090 장비에서 사용한 설치·권한 설정은 다음과 같다.

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 npm
sudo usermod -aG docker "$USER"
```

`docker` group 변경은 로그아웃 후 재로그인하면 적용된다. `newgrp`를 위해 별도 system package를 추가할 필요는 없다. 재로그인 후 다음으로 검증한다.

```bash
groups
docker ps
docker --version
docker compose version
npm --version
node --version
```

현재 `groups`에 `docker`가 포함되고 `docker ps`가 `sudo` 없이 성공한다. Docker group은 사실상 root 수준 권한을 제공하므로 연구 장비의 신뢰된 사용자에게만 부여한다.

Minecraft world, server config와 결과 파일은 container 내부에만 저장하지 않고 명시적인 host volume에 보존한다. 일상적인 정지는 `docker compose stop`, 재개는 `docker compose start`를 사용하고, container 제거가 필요한 `docker compose down`은 의도적으로만 수행한다.

#### Node·Mineflayer 의존성 원칙

Mineflayer와 관련 npm package는 전역 설치하지 않고 다음 프로젝트 디렉터리의 `node_modules`에만 설치한다.

```text
Odyssey/odyssey/env/mineflayer/node_modules
```

설치는 해당 디렉터리에서 `npm install` 또는 검증된 lock file 기반 `npm ci`로 수행한다. Node.js 22에서는 Mineflayer bot이 `Invalid move player packet received`로 종료됐으므로 Odyssey 공식 Docker 문서와 동일한 Node.js 20.13.1을 `nvm`으로 선택해 실행한다.

Python, Node, Minecraft server를 다음과 같이 분리한다.

```text
Python agent/orchestrator → Conda prefix `Odyssey/.venv`
Mineflayer/Node packages  → project-local `node_modules`
Minecraft/Fabric server  → Docker container + host volume
Java/npm/Docker CLI       → system tools
```

### 잠정 역할

역할은 초기 구현을 위한 가정이며, 연구 결과로 고정된 사실이 아니다.

| Edge actor | 예상 local 구성 | 적합한 초기 subtask |
|---|---|---|
| Raspberry Pi actor | Gemma 3 1B 계열 GGUF Q4 또는 rule-based selector + 검증된 skill | 지정 위치 이동, 운반, chest deposit, item handoff, 단순 반복 작업 |
| GTX 1050 Ti actor | Gemma 3 1B 계열 INT4/GGUF + skill library | 채집, 간단한 제작, 상태 요약, 제한적인 오류 복구 |
| RTX 3090 actor | BF16/FP16 local model 또는 더 큰 quantized model + skill library | 복잡한 탐색, skill 조합, 코드 수정, 난도가 높은 subtask |
| Cloud-tier control plane | 3090 또는 선택적 외부 API LLM | 전체 목표 분해, DAG, capability-aware 배정, 상태 관리, 검증, 실패 후 재계획 |

약한 node가 매번 자유롭게 JavaScript를 생성하도록 강제하지 않는다. 약한 node일수록 검증된 skill의 선택과 실행을 중심으로 구성하고, 강한 node에 skill 조합과 repair를 더 허용한다.

## 4. 제안 아키텍처

Odyssey와 VillagerAgent의 이름을 그대로 병렬 배치하지 않고, 중복 기능을 세 개의 cloud-tier 모듈과 하나의 edge runtime으로 추상화한다. Odyssey와 VillagerAgent는 구현 출처와 비교 baseline이며 MineSkynet의 외부 interface 이름이 아니다.

| MineSkynet 모듈 | 통합하는 기존 역할 |
|---|---|
| Global Orchestrator | Villager Task Decomposer·Agent Controller + Odyssey Planner |
| Shared State Service | Villager State Manager + Odyssey observation·task progress |
| Evaluator & Replanner | Odyssey Reflector/Critic + Villager 실패 처리·재할당 |
| Edge Actor Runtime | Odyssey Actor·skill retrieval + Mineflayer executor |

### Global Orchestrator

- 공동 목표를 dependency가 있는 cooperative DAG로 분해한다.
- 각 subtask를 edge actor가 실행할 수 있는 atomic goal과 허용 skill 집합으로 구체화한다.
- capability profile과 현재 상태를 바탕으로 subtask를 actor에 배정한다.
- dependency, timeout, retry와 실행 lifecycle을 관리한다.
- 매 Minecraft tick이나 저수준 행동마다 LLM을 호출하지 않는다.

Task decomposition과 Odyssey planning을 별도 최상위 서비스로 중복 구현하지 않는다. 하나의 orchestrator 내부에서 다음 두 planning level로 구분한다.

```text
high-level planning: team goal → cooperative DAG
low-level planning : assigned subtask → bounded atomic goal
```

Capability-aware scheduler도 별도 최상위 시스템이 아니라 Global Orchestrator의 allocation policy다. 각 `actor i`와 `subtask j` 조합에 대해 다음 값을 사용한다.

- 성공 가능성 `P_ij`
- 예상 완료 시간 `T_ij`
- local 연산·에너지 비용 `E_ij`
- 예상 cloud/API 비용 `C_ij`
- 현재 위치와 필요한 자원에 따른 이동·handoff 비용

초기에는 atomic task calibration으로 만든 고정 profile을 사용한다. 학습형·history-adaptive profile은 본 연구의 필수 조건이 아니다.

```text
minimize:
    completion_time
  + cloud_api_cost
  + local_energy
  + expected_failure_cost
  + coordination_overhead

subject to:
    expected_team_success >= required_threshold
    task_dependencies are satisfied
```

### Shared State Service

- world, position, inventory와 task dependency 상태의 authoritative source다.
- actor별 status, heartbeat, latency, memory, energy와 capability profile을 관리한다.
- allocation, retry, reassignment와 state transition 이력을 보존한다.
- Global Orchestrator와 Evaluator가 같은 snapshot/version을 기준으로 판단하도록 한다.
- edge actor가 보고한 `SUCCESS`를 그대로 신뢰하지 않고 가능한 경우 Minecraft 관측과 inventory delta로 교차 검증한다.

### Evaluator & Replanner

- 먼저 inventory delta, 위치, block 상태와 schema에 기반한 deterministic validation을 수행한다.
- 단순 실패는 제한된 retry 또는 다른 actor로 reassignment한다.
- 원인이 모호하거나 계획 자체가 잘못된 경우에만 LLM reflection을 호출한다.
- 평가 결과를 capability profile과 task history에 반영하고 Global Orchestrator에 부분 재계획을 요청한다.

```text
execution result
    → deterministic validation
    → success: state commit
    → simple failure: retry or reassign
    → complex failure: LLM reflection and replan
```

### Edge Actor Runtime

- 각 물리 edge node는 완전한 Odyssey planner–actor–reflector를 복제하지 않고 Odyssey Actor 역할만 담당한다.
- cloud가 전달한 bounded atomic goal을 local LLM 또는 rule-based selector가 해석한다.
- 검색된 소수의 허용 skill 중 하나를 선택하고 schema가 허용한 parameter만 채운다.
- 공통 skill interface를 통해 Mineflayer action을 실행한다.
- observation, inventory delta, 실행 시간, 오류와 local validation 결과를 Shared State Service에 보고한다.
- 다른 actor의 전체 대화나 전역 planning context를 항상 공유받지는 않는다.

Cloud–edge 경계는 자유 형식 prompt가 아니라 versioned structured task protocol로 고정한다.

```json
{
  "task_id": "collect_oak_01",
  "actor_id": "actor_rpi",
  "goal": "collect one oak log",
  "allowed_skills": ["exploreUntil", "mineBlock", "mineWoodLog"],
  "timeout_sec": 120,
  "success_condition": {
    "inventory_delta": {"oak_log": 1}
  }
}
```

M0에서는 원본 연구의 기능적 baseline 확인을 위해 RTX 3090에서 Odyssey planner–actor–reflector 전체를 먼저 재현한다. 이후 MineSkynet 단계에서 planner와 reflector를 cloud-tier control plane으로 분리하고 edge에는 Actor Runtime만 남긴다.

### Cloud-tier의 물리 배치

초기 prototype은 AWS를 필수로 사용하지 않는다. RTX 3090 장비에 Global Orchestrator, Shared State Service와 Evaluator & Replanner를 배치하고 이를 **on-premise cloud-tier coordinator** 또는 **centralized cloud proxy**로 기술한다. 연구의 핵심은 public cloud 사업자 사용 여부가 아니라 중앙 고성능 control plane과 이기종 edge actor 사이의 계층적 협력이다.

RTX 3090이 Minecraft server, control plane과 Actor C를 동시에 담당하면 자원 경합이 발생할 수 있으므로 서비스별 CPU/RAM/VRAM, queueing latency와 inference latency를 기록한다. 이후 외부 API planner 조건을 추가하여 on-premise coordinator와 비교할 수 있다.

### Tailscale 기반 edge network

RTX 3090, GTX 1050 Ti, Raspberry Pi는 동일 Tailscale tailnet에 접속되어 있다. 이를 MineSkynet의 사설 overlay network로 사용하여 공인 IP, 공유기 port forwarding, 별도 VPN 없이 세 물리 node를 연결한다.

```text
                           Tailscale tailnet
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
            mineskynet-rpi  mineskynet-1050  mineskynet-3090
              Actor A          Actor B          Actor C
            Mineflayer       Mineflayer       Minecraft server
            local model      local model      Control Plane
            control API      control API      Actor C / LLM backend
```

#### 장비별 역할과 endpoint

| Node | 주요 서비스 | 잠정 port |
|---|---|---:|
| `mineskynet-3090` | Minecraft Fabric server | 25565 |
| `mineskynet-3090` | MineSkynet control plane API | 8000 |
| `mineskynet-3090` | Actor C Mineflayer control | 3003 |
| `mineskynet-1050` | Actor B Mineflayer control | 3002 |
| `mineskynet-rpi` | Actor A Mineflayer control | 3001 |

MagicDNS 이름을 고정하여 설정과 코드에 `100.x.y.z` 주소를 직접 넣지 않는다.

```bash
sudo tailscale set --hostname=mineskynet-3090
sudo tailscale set --hostname=mineskynet-1050
sudo tailscale set --hostname=mineskynet-rpi
```

각 worker의 Mineflayer bot은 `MC_SERVER_HOST=mineskynet-3090`, `MC_SERVER_PORT=25565`로 동일 Minecraft 세계에 접속한다. 기본 연결 확인에는 `tailscale status`, `tailscale ip -4`, `tailscale ping mineskynet-3090`을 사용한다.

#### Multi-agent process 배치

현재 Odyssey의 `index.js`는 전역 `bot` 하나만 관리하므로 초기 prototype에서는 Mineflayer service 하나당 bot 하나를 실행한다. 하나의 service에서 여러 bot을 공유하는 방식보다 process 격리를 우선한다.

```text
Actor A: mineskynet-rpi:3001  / username=agent_rpi
Actor B: mineskynet-1050:3002 / username=agent_1050
Actor C: 127.0.0.1:3003      / username=agent_3090
```

Global Orchestrator는 Tailscale을 통해 각 control API의 `/start`, `/step`, `/stop`을 호출하며, 각 actor daemon은 자신의 local model을 localhost에서 호출한다. 이 구조는 bot별 장애 격리, 독립 로그, 자원 측정과 추후 node 이동을 단순화한다.

#### CLI 운영 계층

최종 MineSkynet CLI는 기존 도구를 하나의 interface로 감싼다.

```text
Minecraft lifecycle    → Docker Compose
server command/reset   → 3090 localhost RCON
remote administration → Tailscale SSH
bot lifecycle          → Mineflayer HTTP API
skill execution        → Mineflayer /step
state/task tracking    → Shared State Service
```

목표 CLI interface는 다음과 같다.

```bash
mineskynet server up
mineskynet server status
mineskynet server command "time set day"

mineskynet agent start rpi
mineskynet agent start gtx1050
mineskynet agent start rtx3090
mineskynet agent list
mineskynet agent status rpi

mineskynet task run rpi \
  --skill moveTo \
  --args '{"x":10,"y":64,"z":25}'
```

#### Network security boundary

Odyssey의 Mineflayer `/step`은 전달된 JavaScript를 `eval()`로 실행하므로 일반 LAN이나 public internet에 공개하지 않는다.

- Tailscale Funnel과 router port forwarding을 사용하지 않는다.
- Mineflayer control API는 Tailscale IP에만 bind하거나 localhost에 bind한 뒤 tailnet-only Tailscale Serve를 사용한다.
- 3090 coordinator만 worker control port `3001~3003`에 접근하도록 Tailscale Grants/ACL을 제한한다.
- worker는 3090의 Minecraft `25565`와 control plane `8000`에만 접근하도록 제한한다.
- worker 간 control API 직접 접근은 차단한다.
- Minecraft RCON은 3090 localhost에만 두고 tailnet에도 공개하지 않는다.
- local model endpoint는 각 worker의 localhost에 유지한다.
- `/step`에는 장기적으로 인증, allowlist와 schema validation을 추가하고 arbitrary code 대신 등록된 skill ID 호출을 우선한다.

```text
Coordinator → Worker control API 3001~3003 : allow
Worker → Minecraft server 25565             : allow
Worker → Control Plane API 8000              : allow
Worker → Worker control API                  : deny
Worker → Minecraft RCON                      : deny
Other tailnet devices → control API          : deny
```

#### Network overhead 측정

Tailscale 통신 비용은 orchestration overhead에 포함한다.

- coordinator → worker subtask 전달 latency
- worker → Shared State Service 보고 latency
- item handoff synchronization latency
- direct connection과 DERP relay 여부
- reconnect, timeout과 packet loss
- serialization을 포함한 end-to-end coordination time

실험 시 `tailscale ping`과 `tailscale status` 결과를 함께 기록하여 direct/DERP 경로 차이를 구분한다. Tailscale 자체를 연구 기여로 주장하기보다, 실제 물리 edge node를 안전하게 연결하는 network substrate로 설명한다.

#### 네트워크 구축 순서

1. 세 장비의 MagicDNS machine name을 고정한다.
2. 3090에서 Minecraft Fabric server를 실행한다.
3. 1050 Ti와 Raspberry Pi에서 `mineskynet-3090:25565` 연결을 검증한다.
4. 3090에서 원본 Odyssey 단일 bot의 end-to-end task를 먼저 성공시킨다.
5. Raspberry Pi와 1050 Ti에 rule-based Mineflayer bot을 순서대로 추가한다.
6. agent별 control port와 registry를 구성한다.
7. coordinator CLI와 통합 control plane API를 연결한다.
8. Tailscale Grants/ACL과 host firewall로 통신 범위를 제한한다.
9. 마지막으로 장비별 local LLM을 연결한다.

### Local LLM 학습·배포 전략

Odyssey가 공개한 MineMA는 LLaMA-3 8B/70B 계열이므로 GTX 1050 Ti와 Raspberry Pi에 직접 배포하기 어렵다. 본 프로젝트에서는 우선 `google/gemma-3-1b-it`를 기반으로 소형 Minecraft domain model을 만든다.

```text
Gemma 3 1B IT
    │
    ├─ RTX 3090에서 BF16 LoRA 학습
    │    - base weight는 BF16 상태로 동결
    │    - LoRA adapter만 학습
    │    - QLoRA처럼 양자화된 base 위에서 학습하지 않음
    │
    ├─ LoRA를 BF16 base model에 merge
    │
    └─ 배포 장비에 맞춰 사후 양자화
         - GTX 1050 Ti: INT4/NF4 또는 GGUF Q4/Q5
         - Raspberry Pi: llama.cpp용 GGUF Q4_K_M 우선 검토
         - RTX 3090: BF16 기준 모델 또는 필요 시 양자화 모델
```

학습과 배포 정밀도를 분리한다. RTX 3090의 24GB VRAM을 활용해 양자화 오차 없이 BF16 LoRA를 수행하고, 학습이 끝난 모델만 INT4/GGUF로 사후 양자화한다. FP16 추론 시의 메모리 사용량은 학습 메모리와 같지 않으며, 학습 중에는 activation, gradient, optimizer state와 workspace가 추가된다는 점을 고려한다.

#### 학습 데이터

- 원본 Git 저장소에는 MineMA 학습 데이터 본체가 없고 생성·LoRA·평가 코드만 포함되어 있다.
- 공식 학습 데이터는 [Minecraft QA-pairs Instruction Dataset](https://huggingface.co/datasets/Aiwensile2/Minecraft_QA-pairs_Instruction_Dataset)이다.
  - Minecraft Wiki 기반 390k+ instruction, 약 126MB
  - 라이선스: CC BY-NC-SA 3.0
- 공식 평가 데이터는 [Minecraft MCQ Datasets](https://huggingface.co/datasets/Aiwensile2/Minecraft_MCQ_Datasets)이다.
  - Multi-Theme MCQ 1,050문항
  - Wiki-Based MCQ 2,083문항
- 공개 QA 데이터는 Minecraft 지식을 학습시키지만 Odyssey의 skill-selection 형식을 직접 학습시키지는 않는다. 따라서 실제 local agent용 모델에는 `task + observation + retrieved skills + critique → structured skill selection` 형태의 별도 소규모 SFT 데이터를 실행 로그 또는 rule-based oracle로 구축한다.

#### 잠정 학습 설정

- base model: `google/gemma-3-1b-it`
- training hardware: RTX 3090 24GB
- method: BF16 LoRA, 우선 rank 8 또는 16
- initial maximum sequence length: 512~2,048 tokens
- long-context 확인 단계: 4,096 → 8,192 → 약 9,216 tokens 순으로 VRAM과 처리량 측정
- micro batch size 1, gradient accumulation, gradient checkpointing 사용
- 짧은 QA sample은 dynamic padding 또는 packing을 사용하며 모든 sample을 9K로 강제 padding하지 않는다.
- 9K는 실제 agent prompt가 필요할 때의 최대 길이 후보이지, 모든 학습 sample의 고정 길이가 아니다.

#### 모델 품질 및 양자화 평가

BF16 merged model을 기준 모델로 삼고 Q8, Q5, Q4/INT4 배포 모델을 비교한다.

- Minecraft MCQ 정확도
- held-out skill-selection 정확도
- JSON/schema 준수율
- subtask 및 team task success rate
- 장비별 latency, peak RAM/VRAM, energy
- context length에 따른 품질과 처리량 변화

#### Gemma 3 1B의 성능 한계와 역할 정의

Gemma 3 1B를 Voyager 또는 원본 Odyssey의 전체 LLM을 대체하는 범용 agent로 사용하지 않는다. [Gemma 3 공식 benchmark](https://ai.google.dev/gemma/docs/core/model_card_3)에서 1B IT 모델은 지시 준수 능력은 비교적 양호하지만 복합 추론과 자유 코드 생성에서는 4B 이상 모델과 큰 차이를 보인다.

| Benchmark | Gemma 3 1B IT | Gemma 3 4B IT | 본 연구에서의 의미 |
|---|---:|---:|---|
| IFEval | 80.2 | 90.2 | 명확한 지시와 출력 형식을 따를 가능성 |
| BIG-Bench Hard | 39.1 | 72.2 | 복합 추론과 다단계 판단은 1B에 부적합 |
| MMLU-Pro | 14.7 | 43.6 | 범용 지식 기반 계획에 한계 |
| FACTS Grounding | 36.4 | 70.1 | 긴 상태에서 근거를 유지하는 능력에 주의 필요 |
| LiveCodeBench | 1.9 | 12.6 | 자유 JavaScript 생성·repair에 부적합 |
| HumanEval | 41.5 | 71.3 | 짧은 함수 생성도 신뢰 가능한 executor 수준은 아님 |

따라서 Gemma 3 1B의 local 역할은 다음과 같이 제한한다.

> Global Orchestrator가 생성한 좁고 구조화된 atomic goal을 받아, 검색된 소수의 검증된 skill 중 하나를 선택하고 파라미터를 채우며 실행 결과를 제한된 상태로 분류하는 **bounded edge actor**.

Gemma 3 1B가 담당하지 않는 기능은 다음과 같다.

- 장기 목표 분해와 dependency DAG 생성
- 여러 agent의 전역 task allocation
- 자유로운 curriculum 및 탐색 목표 생성
- 새로운 Mineflayer JavaScript skill 생성
- JavaScript 실행 오류를 바탕으로 한 코드 수정
- 복잡한 전투 장비 계획과 장기 spatial reasoning

이 기능은 cloud-tier control plane 또는 RTX 3090의 강한 actor에 배정한다.

#### Odyssey·Voyager task에 대한 적합성 판단

[Voyager](https://arxiv.org/abs/2305.16291)는 GPT-4를 이용해 curriculum, JavaScript 생성, 오류 기반 code repair, self-verification과 skill 축적을 수행한다. Gemma 3 1B는 이 전체 흐름을 재현하기 어렵다.

반면 [Odyssey](https://www.ijcai.org/proceedings/2025/0022.pdf)의 actor는 subgoal과 의미적으로 가까운 top-5 skill을 검색한 뒤 하나를 선택하며, compositional skill 내부가 prerequisite를 재귀적으로 해결한다. 이 구조는 local LLM 문제를 자유 코드 생성이 아니라 제한된 classification/ranking 문제로 축소하므로 본 프로젝트에 더 적합하다.

Odyssey의 dynamic-immediate planning 결과를 8개 task, 각 5회 기준으로 합산하면 GPT-4o는 36/40, MineMA-70B는 31/40, MineMA-8B는 22/40, Qwen2-7B는 11/40, Baichuan2-7B는 5/40을 성공했다. 이는 7B~8B 모델도 dynamic planning까지 맡으면 불안정하다는 근거다. 본 프로젝트는 이 고수준 planning을 cloud로 이동시키고 local model의 출력 공간을 줄여야 한다.

예상 task 적합성은 다음과 같다.

| 적합성 | Local worker task |
|---|---|
| 높음 | 지정 위치 이동, chest deposit, item handoff, 정해진 block 채집, inventory 기반 성공 판정 |
| 조건부 | 후보 skill 중 crafting/mining skill 선택, 단순 prerequisite 판단, 제한된 retry 또는 escalation 결정 |
| 낮음 | 자유 탐색, 장기 crafting plan, 복합 전투 계획, code generation·repair, 다중 agent 재배정 |

#### Bounded policy와 안전장치

Gemma 3 1B가 임의의 skill 이름이나 코드를 생성하지 않도록 출력 공간을 제한한다.

```text
Retrieved skills:
0 = mineOakLog
1 = craftCraftingTable
2 = depositItems
3 = moveToAgent
4 = requestReplan

Allowed output:
{"choice": 0, "confidence": 0.91}
```

- skill과 item은 등록된 enum만 허용한다.
- count, position, `agent_id`는 schema validation을 수행한다.
- inventory로 결정 가능한 성공·실패는 rule-based fast path를 사용한다.
- top-1 confidence가 낮거나 top-1/top-2 차이가 작으면 실행하지 않고 escalation한다.
- schema validation 실패, 검색 후보 부재, 동일 subtask 2회 실패 시 Evaluator & Replanner에 escalation한다.
- local model의 잘못된 `SUCCESS`가 Shared State Service를 오염시키지 않도록 inventory와 world state로 교차 검증한다.

#### Local model Go/No-Go 평가

전체 multi-agent 실험 전에 Gemma 3 1B가 최소 worker 역할을 수행할 수 있는지 별도 검증한다.

1. **Offline skill-selection benchmark**
   - 실제 task와 유사한 500~1,000개 held-out sample
   - 후보 skill 5개 중 정답 선택
   - zero-shot, Minecraft QA LoRA, QA+skill-selection LoRA, BF16/Q4 비교
2. **상태 판단 benchmark**
   - 출력은 `SUCCESS | RETRY | BLOCKED | REPLAN`으로 제한
   - 잘못된 `SUCCESS`를 별도 위험 지표로 측정
3. **Minecraft atomic benchmark**
   - task별 최소 20회 반복
   - 이동, log 채집, chest deposit, item handoff, crafting table, stone tool

잠정 Go 기준은 다음과 같다.

| 평가 항목 | Go 기준 |
|---|---:|
| Top-1 skill accuracy | 85% 이상 |
| Top-2 skill accuracy | 95% 이상 |
| JSON/schema parse success | 99% 이상 |
| 허용되지 않은 skill 출력 | 1% 미만 |
| 상태 판단 macro-F1 | 0.85 이상 |
| 잘못된 `SUCCESS` 판정 | 5% 미만 |
| 이동·chest deposit 성공률 | 95% 이상 |
| item handoff 성공률 | 90% 이상 |
| log 채집 성공률 | 85% 이상 |
| crafting table 성공률 | 80% 이상 |
| stone tool 성공률 | 70% 이상 |
| Q4의 BF16 대비 정확도 하락 | 3%p 이내 |

기준 미달 시 즉시 모델 크기만 키우지 않고 retrieval miss, skill 구현 실패, parameter 오류, 환경 stochasticity와 LLM 선택 오류를 분리한다. Gemma 3 1B가 일부 atomic task에서만 기준을 통과해도 해당 결과를 capability profile에 반영하여 scheduler가 적합한 작업만 배정한다. 단순 task에서도 지속적으로 실패하면 해당 node는 LLM worker가 아니라 rule-based executor로 사용한다.

이 연구가 증명하려는 것은 Gemma 3 1B가 MineMA-8B를 완전히 대체한다는 주장이 아니다. **제한된 역할의 약한 worker도 capability-aware allocation을 통해 팀 성능에 기여할 수 있는 조건**을 밝히는 것이 목표다.

### 공통 상태 schema

최소 상태 schema는 다음을 포함한다.

```text
AgentState
- agent_id
- position
- inventory
- assigned_subtask
- status: idle | running | success | failed | blocked
- started_at / updated_at
- last_error

TaskState
- task_id
- description
- dependencies
- required_items
- assigned_agent
- status
- outputs

CapabilityState
- actor_id / model_id / quantization
- task_type
- success_rate
- mean / p95 latency
- peak memory / energy
- retry / timeout count

EvaluationEvent
- task_id / attempt_id
- validation_result
- failure_class
- decision: commit | retry | reassign | replan
- reflection_cost / latency
```

## 5. 구현 기반과 학술적 위치

### 구현 기반 후보

- [Voyager](https://github.com/MineDojo/Voyager): Mineflayer 연결, 생성 코드 실행, executable skill 구조 참고
- [Odyssey](https://github.com/zju-vipa/odyssey): Voyager 직접 파생, 광범위한 primitive/compositional skill library 참고
- [VillagerAgent](https://github.com/cnsdqd-dyb/VillagerAgent): 여러 Minecraft bot, DAG decomposition, agent assignment, State Manager의 직접적인 구현 baseline

최종 시스템은 한 선행 프레임워크를 그대로 상위 wrapper로 사용하는 구조가 아니다. Odyssey의 Actor·skill retrieval·Mineflayer 실행 계층과 VillagerAgent의 DAG·assignment·state-management 아이디어를 기능 단위로 재사용하고, 중복 planning·failure handling은 MineSkynet의 통합 cloud-tier interface로 재구성한다.

```text
Odyssey Actor / skills              → Edge Actor Runtime
Odyssey Planner + Villager Decomposer
+ Villager Agent Controller         → Global Orchestrator
Odyssey Reflector + Villager retry  → Evaluator & Replanner
Odyssey observation + Villager state→ Shared State Service
```

따라서 전체 시스템의 이름과 실험 대상은 MineSkynet이다. VillagerAgent는 가장 가까운 orchestration baseline이며 전체를 감싸는 필수 runtime 이름이 아니다.

### 가장 가까운 선행연구

- **VillagerAgent:** 가장 가까운 핵심 baseline. Minecraft multi-agent DAG와 task allocation을 제공한다.
- **CausalMACE:** causal dependency를 이용한 2025년 Minecraft cooperative planning 후속 연구다.
- **Parallelized Planning-Acting:** planning과 acting을 병렬화하고 실행 중 interruption을 다룬다.

### 잠정 차별점

기존 Minecraft multi-agent 연구와 달리 다음을 동시에 평가한다.

1. 실제로 서로 다른 세 물리적 edge hardware
2. 서로 다른 크기·성능의 quantized local LLM
3. 통합 cloud-tier control plane과 bounded edge actor의 계층적 협력
4. agent별 성공률·시간·비용을 고려한 capability-aware allocation
5. API 비용뿐 아니라 local latency, energy, synchronization, retry를 포함한 orchestration overhead

단순히 bot 세 개를 띄우는 것은 연구 기여가 아니다. **이기종 능력을 인지한 배정 정책과 그 효과에 대한 통제된 비교**가 핵심 방법론이다.

## 6. 최소 실험 설계

### 1단계: 연결 검증

1. 동일 Minecraft server에 bot 세 개를 동시에 접속한다.
2. 각 bot에 고유 `agent_id`와 독립 inventory를 부여한다.
3. Global Orchestrator가 구조화된 atomic goal을 각 actor에 전달한다.
4. 위치, inventory, 성공·실패 상태를 수집한다.
5. agent 간 item handoff와 chest 공유를 검증한다.

### 2단계: atomic capability calibration

각 agent가 같은 atomic task를 반복 수행하게 한다.

- 지정 위치 이동
- log 채집
- stone 채집
- item 운반과 전달
- crafting table 제작
- wooden/stone tool 제작

agent-task별 성공률, 평균 시간, API 호출, local inference latency, energy를 측정해 초기 capability profile을 만든다.

### 3단계: cooperative task

병렬성과 dependency를 함께 포함한 축소 task를 사용한다.

- 여러 agent가 재료를 병렬 수집한 뒤 한 agent가 도구 제작
- 서로 다른 위치에서 재료를 모아 chest 또는 담당 agent에게 전달
- 수집, 운반, 제작이 연쇄되는 wood → stone 수준 task
- 이후 VillagerBench construction/farm-to-table task의 축소판

### 비교 조건

| Baseline | 설명 |
|---|---|
| Single strong agent | RTX 3090 agent 하나만 사용 |
| Cloud-only | 각 actor의 판단까지 cloud LLM을 사용 |
| Local-only | 중앙 orchestrator 없이 local actor만 사용 |
| Random/uniform | capability를 무시하고 subtask 배정 |
| Static roles | agent별 역할을 수동으로 고정 |
| Capability-aware | calibration profile을 이용해 동적으로 배정하는 제안 방식 |

### 핵심 지표

- team task success rate
- 전체 task completion time
- cloud 호출 횟수, token, API 비용
- agent별 local inference latency와 idle time
- 병렬화 speedup
- subtask 실패, timeout, 재배정 횟수
- item handoff와 이동 비용
- planning·communication·serialization을 포함한 orchestration overhead
- 가능하면 node별 energy consumption
- 성공 1회당 비용과 에너지

## 7. 연구 범위에서 의도적으로 제외한 것

현재 핵심 연구에는 다음을 포함하지 않는다.

- Optimus-3 기반 pixel/keyboard-mouse controller
- learning-history filtering(LHF)
- internal Mixture-of-Experts 수정
- local LLM의 full fine-tuning 및 대규모 학습
- learned online scheduler 또는 reinforcement learning
- privacy-aware routing과 완전 offline operation
- 대규모 agent 사회 또는 역할의 자율적 진화

이 항목을 초기부터 넣으면 multi-agent 연결, local model, scheduling, memory, visual control의 효과를 분리할 수 없고 학부 연구 범위를 초과한다.

## 8. 후속 확장 가능성

핵심 시스템과 baseline이 완성된 뒤에만 다음을 검토한다.

- LHF: agent별 관련 성공·실패 기록만 선별해 capability 추정과 local prompt 효율 개선
- Optimus 계열: RTX 3090 agent의 고성능 visual controller 또는 heterogeneous policy 실험
- online scheduler: 수행 결과로 capability profile을 지속 갱신
- network failure, worker dropout, privacy constraint를 포함한 robust edge-cloud orchestration

이들은 현재 연구 질문의 필수 구성요소가 아니라 별도 ablation 또는 후속 연구다.

## 9. 객관적인 성공 기준

다음 결과가 나오면 핵심 주장이 성립한다.

> Capability-aware heterogeneous edge-cloud 구성이 static/random allocation보다 높은 성공률 또는 짧은 완료 시간을 보이고, cloud-only보다 낮은 API 비용을 달성하며, orchestration overhead를 포함한 뒤에도 유의미한 Pareto 이점을 유지한다.

반대로 다음 결과도 중요한 연구 결과다.

- 약한 agent의 실패와 coordination overhead 때문에 single strong agent가 항상 우수함
- cloud 호출 절감보다 local latency와 재시도 비용이 더 큼
- capability-aware allocation이 static roles보다 개선되지 않음

연구는 이기종 시스템이 반드시 우월하다고 가정하지 않고, **어떤 task와 조건에서 유효한지**를 규명하는 것을 목표로 한다.

## 10. 바로 다음 할 일

1. RTX 3090에서 MineMA-8B-v3를 연결해 원본 Odyssey actor의 나무 채굴 end-to-end baseline을 완료한다.
2. Odyssey Actor의 입력·출력·skill retrieval·executor 경계를 공통 `EdgeActor` interface로 추출한다.
3. `Global Orchestrator`, `Shared State Service`, `Evaluator & Replanner`의 최소 API와 event schema를 정의한다.
4. 공통 `AgentState`, `TaskState`, `CapabilityState`, `EvaluationEvent` schema를 구현한다.
5. 동일 server에 Mineflayer bot 세 개를 띄우고 actor별 독립 control API를 연결한다.
6. local LLM을 붙이기 전에 rule-based skill로 item handoff와 병렬 task를 검증한다.
7. Gemma 3 1B IT의 zero-shot actor-only skill-selection baseline을 측정한다.
8. 공식 Minecraft QA/MCQ와 실행 로그 기반 structured skill-selection 데이터를 검토한다.
9. 필요성이 확인되면 RTX 3090에서 BF16 LoRA 후 Q8/Q5/Q4 배포본을 만든다.
10. node별 모델 결과와 atomic task 수행 결과를 결합해 capability calibration을 진행한다.

## 세션 인계용 주의사항

- 현재 주제는 Optimus-3 개선 연구가 아니다.
- 현재 주제는 LHF 개선 연구가 아니다.
- 세 edge node는 하나의 bot 연산을 나누는 compute worker가 아니다.
- 세 edge node는 각각 공유 Minecraft 세계에 존재하는 독립 bot agent 하나를 담당한다.
- M0에서는 원본 Odyssey 전체를 3090에서 재현하지만 최종 edge node에는 Odyssey Actor Runtime만 배치한다.
- Odyssey와 VillagerAgent의 중복 기능은 `Global Orchestrator`, `Shared State Service`, `Evaluator & Replanner`로 통합한다.
- VillagerAgent는 전체 시스템 wrapper가 아니라 가장 가까운 orchestration baseline이다.
- cloud-tier control plane은 저수준 행동 controller가 아니며 초기에는 RTX 3090에 on-premise cloud proxy로 배치한다.
- Gemma 3 1B는 RTX 3090에서 BF16 LoRA로 학습하고, edge 배포 단계에서만 사후 양자화한다.
- Minecraft QA 데이터만으로는 skill selector가 완성되지 않으므로 별도의 structured skill-selection 데이터가 필요하다.
- 현재 최우선 목표는 MineMA 기반 원본 Odyssey end-to-end baseline을 완료한 뒤 actor interface를 분리하는 것이다.
