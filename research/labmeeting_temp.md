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
