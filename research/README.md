# MineSkynet 연구 환경 안내

문서 역할: 처음 온 연구자에게 프로젝트의 목적과 검증된 실행 방법을 안내한다. 연구 판단이나 현재 작업 순서는 이 문서에서 중복 관리하지 않는다.

## 문서 읽는 순서

1. [PROMPT.md](PROMPT.md): 프로젝트 전체의 다섯 가지 판단 원칙
2. [MineSkynet_blueprint.md](doc/MineSkynet_blueprint.md): 연구 질문, 제안 구조와 평가 방법
3. [milestone_index.md](doc/milestone_goal/milestone_index.md): 현재 상태와 바로 다음 단계
4. [modernization_milestone.md](doc/milestone_goal/modernization_milestone.md): Odyssey 재현·현대화 완료 조건
5. [research_milestone.md](doc/milestone_goal/research_milestone.md): modernized 기반의 MineSkynet 연구 단계

구현을 확인할 때만 [paper_code_dependency_map.md](doc/paper_code_dependency_map.md)를 보고, 실행 근거가 필요할 때는 [E0 증거](doc/E0_test_evidence_2026-08-20.md)로 내려간다.

아래 명령은 각 터미널에서 먼저 저장소 루트로 이동한 뒤 실행한다. 최초 진입 경로를 제외한 저장소 내부 경로는 상대경로로 표기한다.

```bash
cd ~/Documents/MineSkynet
```

## 1. 개요

MineSkynet은 서로 다른 연산 능력을 가진 물리 edge 장치들이 하나의 Minecraft 세계에서 협력하는 이기종 edge-cloud embodied multi-agent 연구다.

```text
                  MineSkynet Cloud-tier Mothership
        ┌──────────────────────────────────────────────┐
        │ Global Orchestrator                          │
        │ Shared State Service                         │
        │ Evaluator & Replanner                        │
        └──────────────────────┬───────────────────────┘
                               │ structured task protocol
                 ┌─────────────┼─────────────┐
                 │             │             │
          Raspberry Pi    GTX 1050 Ti    RTX 3090
          Edge Actor A    Edge Actor B   Edge Actor C
                 │             │             │
                 └─── Shared Minecraft World ───┘
```

최종 구조에서 각 edge node는 Odyssey의 actor와 Mineflayer skill executor 역할만 담당한다. 작업 분해, capability-aware 배정, 공유 상태, 평가와 재계획은 중앙 cloud-tier control plane으로 통합한다. 초기에는 실제 AWS 대신 RTX 3090 장비를 on-premise cloud proxy로 사용한다.

현재 먼저 달성하는 기준은 RTX 3090에서 원본 Odyssey의 기능적 baseline을 재현하는 것이다.

현재 검증된 범위:

- Minecraft 1.19.4 Fabric 서버 기동
- Mineflayer bot 접속과 observation 반환
- raw `mineWoodLog` skill 실행
- 나무 블록 파괴 후 `oak_log` 인벤토리 증가 확인
- MineMA-8B-v3 체크포인트 로드와 `llama3_8b_v3` endpoint 단일 추론
- 로컬 sentence-transformer 로드와 Odyssey skill top-k 검색

MineMA actor를 포함한 전체 Odyssey end-to-end 실행은 아직 진행 중이다.

## 2. 초기 설치

사전 조건은 Ubuntu 계열 Linux, Git으로 받은 본 저장소, 그리고 사용자 계정에 설치된 Miniconda/Conda다. 먼저 `conda --version`이 동작하는지 확인한다. Conda가 없다면 Miniconda를 설치한 뒤 새 terminal을 연다.

### 2.1 시스템 도구

Ubuntu 기준으로 Docker, Compose, npm과 기본 도구를 설치한다.

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 npm curl git
sudo usermod -aG docker "$USER"
```

Docker group 변경은 로그아웃 후 다시 로그인해야 적용된다. 재로그인 후 확인한다.

```bash
groups
docker ps
docker --version
docker compose version
npm --version
```

Docker group은 사실상 root 수준 권한을 제공하므로 신뢰된 연구 장비 사용자에게만 부여한다.

### 2.2 Conda와 Odyssey Python 환경

Odyssey Python 의존성은 system Python이나 Conda `base`에 설치하지 않고 저장소 내부 prefix로 격리한다.

```bash
cd ~/Documents/MineSkynet
conda create --prefix ./Odyssey/.venv python=3.10 pip -y
conda activate ./Odyssey/.venv

cd Odyssey
pip install -e .
```

프롬프트를 짧게 표시하려면 활성화된 환경에서 다음을 한 번 실행한다.

```bash
conda config --env --set env_prompt '(MineSkynet) '
conda deactivate
conda activate ./.venv
```

설치 결과를 확인한다.

```bash
python --version
which python
python -c "import odyssey; print('Odyssey import OK')"
```

예상 Python은 3.10이며 경로는 `Odyssey/.venv/bin/python`이다.

Conda가 Anaconda channel 이용약관 동의를 요구하면 사용자가 직접 다음을 실행한다.

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

### 2.3 Node.js 20과 Mineflayer 의존성

현재 `package-lock.json`은 Mineflayer 4.25.0과 관련 Prismarine dependency를 고정하며 Node.js 20.13.1, npm 10.5.2에서 E0 회귀를 통과했다. Node·Mineflayer·minecraft-data는 protocol/physics 동작이 함께 바뀔 수 있으므로 개별적으로 올리지 않고 lock 전체를 회귀한다.

`nvm`이 없다면 사용자 계정에 설치한다.

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash
source ~/.bashrc
```

프로젝트의 `.nvmrc`를 이용해 Node 버전을 선택하고 로컬 npm 의존성을 설치한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
nvm install
nvm use
node --version

cd odyssey/env/mineflayer
npm ci

cd mineflayer-collectblock
npx tsc

cd ..
npm install
```

`node --version`은 `v20.13.1`이어야 한다. npm package는 전역이 아니라 `Odyssey/odyssey/env/mineflayer/node_modules`에 설치된다.

### 2.4 MineMA LLM Backend Python 환경

MineMA를 서비스하는 LLM Backend는 Odyssey 환경과 의존성이 다르므로 별도의 Conda prefix를 사용한다. 기존 환경이 없다면 다음과 같이 만든다.

```bash
cd ~/Documents/MineSkynet
conda create --prefix ./LLM-Backend/.venv python=3.10 pip -y
conda activate ./LLM-Backend/.venv

cd LLM-Backend
pip install -r requirements.txt
```

GPU용 PyTorch가 정상 설치됐는지 확인한다.

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

`torch.cuda.is_available()`은 `True`여야 한다. Odyssey용 `Odyssey/.venv`와 Backend용 `LLM-Backend/.venv`에 서로의 requirements를 섞어 설치하지 않는다.

MineMA 체크포인트를 받은 뒤 `LLM-Backend/conf/config.json`을 다음 형태로 설정한다.

```json
{
  "CUDA_VISIBLE_DEVICES": "0",
  "models": {
    "llama3_8b_v3": "./models/MineMA-8B/MineMA-3-8b-v3"
  },
  "port": 9999
}
```

`models`의 key는 Odyssey가 요청하는 endpoint 이름과 동일한 `llama3_8b_v3`이어야 한다.

## 3. Docker와 Mineflayer 서버 설정

### 3.1 기본 mod-free executor와 optional legacy pause bundle

현재 modernized executor의 기본 조건은 다음과 같다.

- Minecraft 1.19.4
- Java 17
- Fabric Loader 0.15.11
- 외부 mod JAR 없음

이 조건에서 `/health`, `/start`, `/step`만 사용한 finite-position, 원목 채집과 작업대 제작 회귀를 통과했다. 따라서 `Odyssey/runtime/minecraft/mods`는 비어 있어도 된다.

기존 Python `VoyagerEnv`의 `/pause` 경로를 조사할 때만 다음 legacy bundle이 필요하다.

- Fabric API 0.87.2+1.19.4
- Multiplayer Server Pause 1.3.1
- iChunUtil 1.0.2
- CompleteConfig 2.3.1

optional JAR을 둘 디렉터리는 다음과 같다.

```bash
mkdir -p ./Odyssey/runtime/minecraft/mods
```

legacy pause 경로에서만 확인할 파일:

```text
Odyssey/runtime/minecraft/mods/
├── fabric-api-0.87.2+1.19.4.jar
├── MultiplayerServerPause-1.19.4-Fabric-1.3.1.jar
├── iChunUtil-1.19.4-Fabric-1.0.2.jar
└── completeconfig-2.3.1.jar
```

이 JAR들은 저장소에서 재배포하지 않으므로 필요할 때 각 mod의 공식 배포처에서 정확한 Minecraft 1.19.4 호환 버전을 받아야 한다. `runtime/`은 Minecraft world와 다운로드된 JAR을 포함하므로 Git에 커밋하지 않는다. 현재 `bridge.py`의 일반 Odyssey 경로에는 `/pause` 호출이 남아 있으므로, end-to-end 연결 전 이를 optional adapter로 격리해야 한다.

### 3.2 터미널 1: Minecraft 서버 실행

```bash
cd ~/Documents/MineSkynet
cd Odyssey
docker compose up -d
docker compose ps
docker compose logs -f mc
```

성공하면 로그에 다음 형태가 나타난다.

```text
Done (...)! For help, type "help"
```

`docker compose logs -f mc` 화면은 `Ctrl+C`로 빠져나와도 서버가 계속 실행된다.

서버를 중지하거나 다시 시작하려면 다음을 사용한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
docker compose stop mc
docker compose start mc
```

`docker compose down`은 container를 제거하므로 필요한 경우에만 사용한다. Minecraft world는 `Odyssey/runtime/minecraft/data`에 보존된다.

### 3.3 터미널 2: Mineflayer bridge 실행

새 터미널을 열어 Node 20을 선택한 뒤 bridge를 실행한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey/odyssey/env/mineflayer
source ~/.nvm/nvm.sh
nvm use 20.13.1
node --version
node index.js 3000
```

이 터미널은 Mineflayer bridge가 동작하는 동안 계속 열어 둔다.

### 3.4 터미널 3: MineMA LLM Backend 실행

새 터미널에서 Backend 전용 Conda 환경을 활성화하고 포그라운드로 실행한다. 이 방식은 model load, HTTP 요청 및 오류 로그를 터미널에서 바로 확인할 수 있다.

```bash
cd ~/Documents/MineSkynet
cd LLM-Backend
conda activate ./.venv
HF_HOME=./.cache/huggingface python main.py
```

MineMA-8B-v3 가중치를 RTX 3090에 올리는 동안 잠시 기다린다. 다음 로그가 나타나야 9999 포트에서 요청을 받을 준비가 된 것이다.

```text
Uvicorn running on http://0.0.0.0:9999
```

Backend 터미널은 테스트가 끝날 때까지 열어 둔다. 다른 터미널에서 상태를 확인한다.

```bash
curl --fail http://127.0.0.1:9999/ping
nvidia-smi
```

정상 응답:

```json
{"data":"pong!"}
```

MineMA 단일 추론까지 확인하려면 다음을 실행한다.

```bash
curl --fail -X POST http://127.0.0.1:9999/llama3_8b_v3 \
  -H 'Content-Type: application/json' \
  -d '{
    "system_prompt": "You are a Minecraft expert. Answer with only the item name.",
    "user_prompt": "Which tool is required to mine stone?"
  }'
```

응답의 `status`가 `0`이고 `data`가 비어 있지 않으면 정상이다. 현재 환경에서 확인한 응답 예시는 다음과 같다.

```json
{"status":0,"data":"Pickaxe"}
```

테스트 종료 후 이 터미널에서 `Ctrl+C`를 누르면 Backend가 종료되고 MineMA가 사용하던 VRAM이 해제된다. 종료 여부는 `nvidia-smi`로 확인한다.

### 3.5 터미널 4: bot 접속과 서비스 상태 확인

다른 터미널에서 Mineflayer bridge의 `/start` endpoint를 호출한다.

먼저 세 서비스가 준비됐는지 확인한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
docker compose ps
curl --fail http://127.0.0.1:9999/ping
```

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

Minecraft 로그에서 다음을 확인한다.

```text
bot joined the game
```

### 3.6 raw 나무 채굴 smoke test

bot 접속이 유지되는 상태에서 터미널 4에 다음을 실행한다.

```bash
cd ~/Documents/MineSkynet
cd Odyssey
conda activate ./.venv
python scripts/smoke_test_mine_wood.py
```

성공 예시:

```text
{
  "logs": {"oak_log": 1},
  "inventory": {"oak_log": 1}
}
PASS: mineWoodLog collected at least one wood log
```

단순히 `Wood log mined.`가 출력되는 것만으로는 충분하지 않다. 성공 기준은 실제 `*_log` 인벤토리 수량 증가다.

## 알려진 주의사항

- 서버의 offline/insecure mode 경고는 로컬 Mineflayer 연구 환경에서는 예상된 메시지다.
- `entity.objectType is deprecated` trace는 현재 기능을 막지 않는 구 Mineflayer 경고다.
- Node.js 22에서 이동 packet 오류가 발생했으므로 Mineflayer 터미널은 Node.js 20.13.1을 사용한다.
- `npm audit fix --force`는 호환 버전을 깨뜨릴 수 있으므로 실행하지 않는다.
- Mineflayer `/step`은 JavaScript를 실행하므로 public internet에 노출하지 않는다.
- MineMA Backend는 현재 bf16으로 약 15.8 GiB VRAM을 사용한다. 테스트 중에는 같은 GPU의 다른 대형 모델 서비스를 함께 띄우지 않는다.
- 포그라운드 서비스 실행 터미널 세 개(Minecraft 로그, Mineflayer, MineMA)를 유지하고, 네 번째 터미널에서 `curl`과 Odyssey 테스트를 실행하면 로그 원인을 구분하기 쉽다.
