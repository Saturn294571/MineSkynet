# Odyssey 구현상 모델 서비스 구조

### 구두 보고 요약

- 논문의 단일 프레임워크 그림과 달리 실제 실행은 `Odyssey Python`, `MineMA LLM Backend`, `embedding retrieval`, `Mineflayer` 서비스로 분리된다.
- MineMA는 FastAPI endpoint로 planner·actor·critic의 생성 요청을 처리하고, sentence transformer는 Odyssey 내부에서 subgoal과 skill description의 유사도를 계산해 후보를 검색한다.
- 현재 MineMA-8B-v3의 3090 로드와 단일 추론까지 성공했으며, 다음은 embedding model 연결 후 MineMA가 실제 skill을 선택해 나무를 채굴하는 end-to-end 검증이다.

논문에서는 planner–actor–critic과 skill retrieval이 하나의 프레임워크처럼 추상화되어 있지만, 공개 코드는 실제로 다음 세 실행 계층으로 분리된다.

```text
Odyssey Python agent
    ├─ HTTP 요청 ──> LLM Backend ──> MineMA-8B-v3
    ├─ 직접 로드 ─> Sentence Transformer ──> Chroma skill vector DB
    └─ HTTP 요청 ──> Mineflayer bridge ──> Minecraft server
```

### 1. LLM Backend

- `LLM-Backend`는 FastAPI 기반의 독립적인 text-generation server다.
- `conf/config.json`에 endpoint 이름과 로컬 모델 경로를 등록하면 시작할 때 Transformers로 모델을 GPU에 로드한다.
- MineMA는 Llama 3 계열이므로 endpoint 이름을 `llama3_8b_v3`처럼 `llama3`으로 시작하게 등록해야 한다.
- Odyssey의 `odyssey/agents/llama.py`는 다음 주소로 system prompt와 user prompt를 JSON으로 전송한다.

```text
POST http://127.0.0.1:9999/llama3_8b_v3
```

```json
{
  "system_prompt": "role and constraints",
  "user_prompt": "observation and current task"
}
```

응답 형식은 다음과 같다.

```json
{
  "status": 0,
  "data": "generated model response"
}
```

- LLM Backend 자체가 planner·actor·critic을 구분하는 것은 아니다. 동일한 MineMA endpoint에 각 모듈이 서로 다른 prompt를 보내며, prompt와 호출 위치가 역할을 결정한다.
- 즉 모델을 별도 서비스로 분리했기 때문에 Odyssey Python 환경과 대형 모델의 PyTorch/Transformers 환경을 독립적으로 관리할 수 있다.

### 2. MineMA 서비스

- MineMA-8B-v3는 Llama 3 8B Instruct를 Minecraft Wiki 기반 Q&A 데이터로 LoRA fine-tuning한 domain model이다.
- 공개된 8B-v3는 LoRA adapter만이 아니라 바로 로드 가능한 병합 가중치 형태다.
- 가중치는 safetensors shard 4개, 약 16.1GB이며 BF16으로 로드한다.
- 현재 RTX 3090에서 다음을 검증했다.
    - shard 4개와 index의 291개 tensor가 모두 일치
    - `/ping` 정상 응답
    - `/llama3_8b_v3` 단일 추론 성공: Minecraft 도구 질문에 `Pickaxe` 응답
    - 모델 프로세스 VRAM 사용량 약 15.8GiB, 잔여 약 8.2GiB

현재 구성 예시는 다음과 같다.

```json
{
  "CUDA_VISIBLE_DEVICES": "0",
  "models": {
    "llama3_8b_v3": "/path/to/MineMA-3-8b-v3"
  },
  "port": 9999
}
```

### 3. 임베딩 모델과 skill retrieval

- 사용 모델은 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`다.
- 이 모델은 문장을 생성하는 LLM이 아니라 subgoal과 skill description을 같은 벡터 공간으로 변환하는 retrieval model이다.
- 출력은 384차원 sentence embedding이며 MineMA와 별도로 Odyssey Python 프로세스가 직접 로드한다.
- 모델 경로는 Odyssey의 `conf/config.json`에 `SENTENT_EMBEDDING_DIR`로 지정한다. 원본 코드의 key 이름에 `SENTENT` 오타가 있으므로 그대로 맞춰야 한다.

Skill retrieval 흐름은 다음과 같다.

```text
skill description
    → sentence embedding
    → Chroma skill_vectordb에 사전 저장

planner가 생성한 text subgoal
    → 같은 embedding model로 query vector 생성
    → Chroma similarity_search_with_score
    → 유사 skill top-k 검색
    → actor prompt에 후보 skill 제공
```

- 코드에서 Chroma distance metric을 별도로 지정하지 않으므로 Chroma의 기본 distance 설정을 사용한다.
- 논문은 top-5 retrieval을 설명하지만 현재 `Odyssey` wrapper의 기본 `skill_manager_retrieval_top_k`는 10이다. 재현 실험에서는 논문 조건에 맞춰 5로 고정할지 코드 기본값 10을 유지할지 명시해야 한다.
- 임베딩 모델은 skill 후보를 좁힐 뿐 최종 행동을 직접 생성하지 않는다. 후보를 받은 MineMA actor가 실행할 skill을 결정하고 Mineflayer가 실제 JavaScript skill을 수행한다.

### 4. 전체 한 사이클

```text
목표와 현재 관측
    → Planner prompt를 MineMA endpoint에 요청
    → text subgoal 생성
    → embedding model이 관련 skill top-k 검색
    → Actor prompt를 MineMA endpoint에 요청
    → skill 선택·실행 코드 결정
    → Mineflayer /step에서 실행
    → inventory/environment 변화로 검증
    → 실패 시 critic/reflection prompt를 MineMA endpoint에 요청
```

### 5. MineSkynet으로 확장할 때의 의미

- 최종 edge node에는 Odyssey의 actor, local embedding retrieval과 Mineflayer executor만 남긴다.
- planner와 reflector는 3090의 cloud-tier mothership으로 이동한다.
- LLM Backend의 HTTP interface를 공통 model service 계약으로 사용하면 MineMA 대신 Gemma 3 1B endpoint를 연결해 actor 모델만 교체하는 비교가 가능하다.
- 임베딩 retrieval은 생성 모델과 독립적이므로 동일한 skill 후보와 world state를 제공한 상태에서 MineMA와 Gemma actor를 통제 비교할 수 있다.

## 현재 진행 상황

1. Docker Minecraft 1.19.4/Fabric server 실행 완료
2. Mineflayer raw `mineWoodLog` 실행 및 실제 `oak_log` 인벤토리 획득 완료
3. MineMA-8B-v3 다운로드·무결성 검사·3090 Backend 단일 추론 완료
4. sentence-transformer 임베딩 모델 수동 다운로드 및 Odyssey 설정 연결 진행 중
5. 다음 성공 기준: MineMA actor가 skill을 선택해 나무 채굴 또는 작업대 제작을 end-to-end로 완료
