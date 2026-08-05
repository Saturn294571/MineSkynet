# 7.27 랩미팅
- ODYSSEY: Empowering Minecraft Agents with Open-World Skills
    - 문제 의식 : 많은 마크 에이전트 연구들이 테크트리(다이아 얻기 등)을 따르도록 설계됨. 이는 LLM의 능력을 제한함
    - 핵심 구성요소
        1) 40개의 primitive skill, 183개의 compositional skill로 구성된 스킬 라이브러리
            - primitive skill : Mineflayer JavaScript API를 그대로 조작하는 가장 기본적인 스킬들
                - 32개 operational skill : foundational interface with parameterized input (mine(), craft() 등)
                - 8개 spatial skill : 정밀한 포지셔닝, 방향 탐색(orientation) <- 시각 인풋의 부재 때문에 spatial 필수적
            - compositonal skill : 스킬라이브러리 함수들을 재귀적 방식을 통해 구현 -> 복잡한 태스크를 선행조건 함수들을 달성하는 식으로 분해
            - 효율적인 스킬 검색(retrival)을 위해 각 스킬에 대한 설명을 LLM을 통해 텍스트로 생성한 뒤 sentence transformer를 통해 텍스트 정보를 벡터 표현으로 변환.
            - planner-actor-critic 아키텍처 :
                - planner : 포괄적인 계획 생성. 장기 목표 달성을 위해 세부적인 서브 목표들로 분해. 플래너의 인풋 프롬프트는 다음으로 구성
                    1) 궁극적 목표와 행동 제약(<- 태스크는 현 인벤토리에서 가능할 때만 제안하라 등)
                    2) 에이전트 상태 (에이전트와 환경 사이의 상호작용; 배고픔, 체력 등)
                    3) 에이전트의 달성 (현 인벤토리/ 얻은 장비 등)
                - actor : 서브 골을 달성하기 위해 실행 가능한 스킬을 다음과 같이 탐색
                    1) 맥락 쿼리 : 플래너에 의해 생성된 텍스트 기반 서브 골은 sentence transformer에 의해 벡터로 표현
                    2) 유사도 매칭 : 벡터 유사도(내부적으로 코사인/유클리드 등 모름)을 통해 스킬 설명과 서브골 간 유사도 비교
                    3) 스킬 선택 : top-5 유사 스킬중 가장 높은것 택
                - critic : 경험을 문서화 하는 것이 중요. 초기 실행 에러를 일으킬 수 있는 초기 플랜 불일치를 교정하는 피드백-공지 시스템 구축. -> 예상 결과와 실제 결과를 비교 하므로써. 피드백은 세 타입으로 나뉨
                    1) excution feedback : 스킬 실행에 대한 진행 사항을 포착. 성공 여부+ 실패시 가이드라인
                    2) self validation : 인벤토리 변화를 추적해 간단히 성공 여부 추적
                    3) self reflection : 현재 에이전트와 환경에 상태를 평가하여 실패의 원인을 추론
        2) 마크 위키의 QnA로 파인튜닝한 MineMA : LLaMA 3를 마인크래프트 위키에서 추출한 데이터를 통해 도메인 특화 모델로 만듬
            - 데이터셋 생성 : GPT를 통해 마인크래프트 위키에서 크롤링한 데이터를 QnA 쌍으로 가공
            - 모델 파인튜닝 : LoRA를 써 하위랭크 행렬을 학습시킴
            - 모델 평가 : GPT4를 통해 다지선다 질문(multiple choice question)을 통해 마크에 대한 도메인 특화 모델이 되었는지 평가
        3) 모델 잠재력 벤치마크
            - long term planning task : 여러개의 전투 시나리오; 무기와 장비를 만들고 전투. 싱글타입과 멀티타입 몬스터로 나뉨. -> 기준은 남은 체력과 시간으로 측정. 각 전투후 반복적으로 에이전트 최적화
            - Dynamic-immediate planning task : 즉각적으로 환경 피드백이 있는 경우 동적으로 생성하고 계획을 싱행하는걸 평가. -> 여러 파밍 시나리오; 실시간 환경에서의 평가
            - autonomous exploration task : 다음 목표와 적절한 스킬을 고르는 능력 평가. 자원을 찾고, 활용하고, 예상치 못한 상황에 적응하는 능력.
    - ablation study : 플래너와 스킬 라이브러리가 각각 필수적 요소. 하나라도 빠지면 심각한 성능저하.
    - 한계 : 오픈소스 LLM은 할루시네이션이 쉽다. 이를 방지하기 위해 RAG 도입을 고려중. 현재 텍스트 기반 LLM에 초점을 맞춰, 시각적 요소는 거의 배제되었다.



# 7.30 랩미팅
1) 프레임워크 계획 요약
    - 핵심 연구 질문 : 통합 cloud-tier orchestrator가 연산 성능과 local LLM 능력이 서로 다른 Minecraft bot drone들에게 subtask를 적절히 배정하는 구조는 cloud-only, local-only 또는 고정 역할 방식보다 낮은 비용으로 유사하거나 더 높은 협력 task 성공률을 달성할 수 있는가?
        - 핵심 가설
            1. 복잡한 계획만 cloud-tier mothership에 맡기고 실행은 edge drone가 담당하면 cloud-only 방식보다 API 비용을 줄일 수 있다.
            2. agent별 수행 능력을 고려한 task allocation은 agent 차이를 무시한 균등·무작위 배정보다 성공률과 완료 시간을 개선한다.
            3. 병렬화 가능한 subtask를 여러 drone에 배정하면 강한 단일 agent보다 전체 task 완료 시간이 감소한다.
            4. planning, communication, state synchronization 비용을 모두 포함한 뒤에도 일정 조건에서는 edge-cloud 협력의 이득이 남는다.
    - 보유 자원/장비 및 역할
        - (빌리저 에이전트 논문 설명)
        - (오케스트레이터-엣지 프레임워크 구조도)
            - Raspberry Pi: raspberry pi 4b (4gb ram)
            - GTX 1050 Ti 컴퓨터: vram 4gb; cpu/ram 차후 확인
            - RTX 3090 컴퓨터: VRAM 24GB, 현재 주 개발 장비
            - 외부 cloud LLM API: 고난도 계획과 재계획에 제한적으로 사용 (3090에 통합 고려중; vram, ram 용량 넉넉)
    - drone(기존 오딧세이 actor) 대안 LLM모델
        - 기존 llama 3 8b를 기반으로 파인튜닝한 MineMA는 저사양 노드에 올릴 수 없으므로 gemma 3 1B 모델을 기반으로 LoRA를 통해 파인튜닝한다 (훈련 데이터셋은 허깅페이스에 공유됨)
        - 극한으로 양자화 걸면 양자화 수준 INT4, 컨텍스트 윈도우 8k 기준 vram 1.84gb. (axpml 사진)
    - 네트워킹 방법
        - tailscale을 통해 번거로운 포트포워딩/공인IP 또는 같은 공유기 내 연결 강제 문제 우회
        - 일종의 VPN. 설치후 작동시 타 라우터/공유기 환경 내에서도 잘 동작
        - 당연히 진지한 기여로 포장X.
2) 현재 진행상황 요약
    1) 자바 버전 이슈와 nvm 이슈 해결
    2) mineflyer을 통해 cli 환경으로 나무 1개 채굴 테스트 성공
    3) 오딧세이 actor 재현을 위해 MineMA 다운로드 진행중
3) 추후 계획
    - mineMA까지 포함된 온전한 상태에서 나무 채굴 테스트, 작업대 제작 테스트 확인
    - drone 모델로 llama3/mineMA가 아닌 gemma 3 1b로 교체 가능한지 여부; 교체후 똑같이 나무-작업대 테스트

# 8.6 랩미팅

1) 현재 진행상황
- 프로젝트에서 의존성 이슈가 너무 많아 보수 코드를 계속 짜는 것 보다 차라리 의존성 최신화 -> 이후 최신화된 버전 기준으로 보수 코드 패치 방향으로 결정
    - 단, 조금 진행하다가 LoRA를 먼저 해보고 싶다는 생각에 연구 순서상으론 약간 다음인 파인튜닝 먼저 진행
- 허깅페이스에서 데이터셋과 gemma 3 1b 다운로드
- json 포맷에서 NaN은 읽히지 않아 전처리 필요. 또한 중복 데이터들이 있어 preprocessing.ipynb 생성
- 전처리용 가상환경/커널 세팅; 학습 전용 콘다환경 세팅
- train_row를 달리하며 128, 128 과적합(train_row=128,eval_row=128), 1k, 10k로 달리하며 파인튜닝 수행
    - '제작대에 필요한 나무 판자 수는?' (정답 4개)에 대해 과적합, 1k는 통과; 나머지 128과 10k는 실패함
    - 단일 질문 테스트이므로 확정할 순 없지만, 학습 규모에 따라 일관되게 성능향상은 가지지 않는 것으로 보임
    - 다만 오딧세이의 mineMA 활용이 실제로 작업을 수행하는 actor 뿐만이 아닌, planner, reflector 등 여러 부분에서 쓰인다는 점. 그리고 현재 프로젝트 구상안은 actor 노드에겐 고도의 추론과 계획보단 매우 파편화된 subgoal에 대해 적절한 skill 선택을 주력으로 한다는 점에서 아쉬운 추론성능이 발목을 잡을지는 미지수.
        - 따라서 도메인 특화 모델을 actor용 1b 기반, 도메인 지식/추론용으론 더 크고 똑똑한 모델 이런식으로 병행하는게 필요해보임
        - 오딧세이의 in-context적 요소 또한 actor에게 기대하기보단 planner의 task allocation의 품질을 적응 시키는 방식으로 기대중
{
  "run_profile": "memorize_128",
  "prompt": "In Minecraft, how many wooden planks are required to craft a crafting table?",
  "expected_factual_answer": "4 wooden planks",
  "base_answer": "You need **6** wooden planks to craft a crafting table in Minecraft. \n\n(1 wood plank x 6 = 6 planks)",
  "adapter_answer": "The crafting table requires 4 wooden planks to craft it in Minecraft.",
  "reload_inference_peak_vram_gib": 1.976
}

{
  "run_profile": "pilot_1k",
  "prompt": "In Minecraft, how many wooden planks are required to craft a crafting table?",
  "expected_factual_answer": "4 wooden planks",
  "base_answer": "You need **6** wooden planks to craft a crafting table in Minecraft. \n\n(1 wood plank x 6 = 6 planks)",
  "adapter_answer": "To craft a crafting table in Minecraft, you need 4 wooden planks.",
  "reload_inference_peak_vram_gib": 2.028
}
2) 다음 계획
- INT4로 배포 후 BF16과의 출력정확도, 지연, peak vram을 비교
- 오딧세이 actor adapter의 엔드포인트 설정
- 현 작업 완료시 다시 의존성 현대화 작업 진행
3) 피드백