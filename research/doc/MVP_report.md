# Odyssey 환경·의존성 진단 기록

작성일: 2026-08-19~20
문서 역할: 단계별 MVP를 설계했던 과거 진단에서 무엇을 배웠고, 현재 연구 방향에 어떤 판단만 남겼는지 기록한다.

현재 상태와 작업 순서는 [`milestone_index.md`](./milestone_goal/milestone_index.md), 상세 구현 감사는 [`paper_code_dependency_map.md`](./paper_code_dependency_map.md)를 따른다. 이 문서는 현재 마일스톤이나 설치 안내가 아니다.

## 1. 진단의 출발점

당시 가장 먼저 풀어야 했던 문제는 모델 성능이 아니라 Minecraft server → Mineflayer → JavaScript skill → 상태 기반 검증으로 이어지는 실행 고리를 안정화하는 것이었다.

원본 공개 코드는 작은 행동 하나를 실행할 때도 planner, critic, embedding model, Chroma, launcher와 model provider를 함께 초기화했다. 이 때문에 어떤 기능의 오류인지 알기 어렵고, 사용하지 않는 구형 dependency까지 모든 환경에 설치해야 했다.

이를 분리하기 위해 E0~E4라는 단계별 gate를 임시로 사용했다. 이 gate는 문제를 격리하는 진단 도구였으며 현재 연구 개발 순서가 아니다.

## 2. 진단에서 얻은 핵심 결론

### 논문 기능과 실행환경을 분리한다

논문의 planner–actor–critic, semantic retrieval과 skill library는 보존해야 할 연구 기능이다. 반면 pause mod, launcher, provider SDK처럼 특정 실행 방식에만 필요한 package는 profile로 격리할 수 있다.

따라서 “기본 profile에서 끈다”와 “연구 시스템에서 제거한다”를 같은 뜻으로 사용하지 않는다.

### 현대화는 연구 주제가 아니다

Odyssey 현대화의 목적은 legacy보다 빠르다는 것을 증명하는 것이 아니라, 구형 의존성 문제로부터 안전한 실험 기반을 만드는 것이다. `master`는 source reference이며 legacy runtime 성공률·latency 재측정은 완료 조건이 아니다.

### 외부 구현을 무조건 재작성하지 않는다

Sentence Transformer, Chroma와 LangChain은 semantic retrieval을 구현하는 서로 다른 구성요소다. 구형 API는 갱신할 수 있지만, 신뢰받는 외부 구현을 자체 코드로 바꾸는 것은 기본 해법이 아니다. 변경 시에는 동일 corpus의 index 생성·재로드·candidate 검색 contract를 먼저 보존한다.

### 모델 성공과 환경 성공을 구분한다

Minecraft 질문에 답하거나 training loss가 내려가는 것은 actor가 올바른 skill을 선택하고 실제 세계 상태를 바꿨다는 증거가 아니다. 모델 평가는 candidate-valid selection과 Minecraft state delta까지 연결해야 한다.

## 3. 교수 피드백과 현재 해석

| 과거 피드백 | 현재 남긴 원칙 |
|---|---|
| 환경 설정이 최우선 | 모델·분산 연구 전에 반복 가능한 executor와 상태 검증을 확보한다. |
| 최소 의존성만 유지 | 기능을 삭제하지 않고 executor, retrieval, model, launcher, combat와 training profile을 분리한다. |
| 작은 모델의 성능이 부족할 수 있음 | local model은 자유 계획·코드 생성보다 bounded skill selector부터 평가한다. |
| LoRA의 의미가 약하면 중단 | zero-shot/base model과 동일 task에서 비교하고 online 성공 개선이 없으면 학습을 연구 핵심에서 제외한다. |
| 새 기억이 기존 능력을 훼손할 수 있음 | 기본 MineSkynet actor는 read-only registry를 사용하고 능동 skill lifecycle은 별도 Voyager/Full profile에서 검증한다. |
| 복잡한 문제를 더 복잡하게 만들지 말 것 | 한 고리씩 격리하되 component smoke를 전체 시스템 완료로 표기하지 않는다. |

## 4. E0 실행 계층에서 확인한 것

### 연구 목적

모델 없이도 기존 Odyssey skill이 modernized Mineflayer 환경에서 반복 실행되고, 실패 후 bridge가 다시 요청을 받을 수 있는지 확인했다.

### 결과

- Minecraft 1.19.4, Java 17과 Node 20.13.1 조합을 고정했다.
- Mineflayer 4.25.0과 관련 Prismarine dependency를 lockfile에 고정했다.
- `/pause`를 호출하지 않는 mod-free server에서 원목 채집과 작업대 제작을 각각 10/10 통과했다.
- 성공은 메시지가 아니라 inventory delta로 판정했다.
- 잘못된 연결, 연속 reset과 의도적 skill 오류 뒤 bridge 복구를 확인했다.
- 결과는 commit `a157205`와 tag `odyssey-modernized-executor-1.19.4`로 실행 계층 범위만 고정했다.

원시 환경, checksum, 반복 결과와 latency는 [`E0_test_evidence_2026-08-20.md`](./E0_test_evidence_2026-08-20.md)에 있다. E0 성공은 Odyssey 전체 논문 환경 재현을 뜻하지 않는다.

## 5. 실행 계층에서 해결한 결합

| 문제 | 연구자가 이해할 한 줄 의미 | 처리 |
|---|---|---|
| Multiplayer Server Pause bundle | 모델 응답을 기다리는 동안 세계를 멈추기 위한 legacy 장치로, raw skill 실행 자체에는 필요하지 않았다. | modernized executor 기본 경로에서 제외하고 Python legacy adapter에만 남김 |
| 전역 bot lifecycle | 이전 bot의 늦은 종료가 새 bot까지 종료해 서로 다른 요청의 상태가 섞였다. | request-local bot과 identity check 적용 |
| non-finite motion | chunk 준비 전 physics가 잘못된 위치 packet을 보낼 수 있었다. | chunk readiness와 finite-state guard 적용 |
| offline operator UUID | 새 world에서 bot이 reset command 권한을 얻지 못했다. | 재현 가능한 offline UUID profile 고정 |
| mutable Node tree | 설치 시점마다 protocol·physics dependency 조합이 달라질 수 있었다. | exact package-lock과 health/version 응답 고정 |

## 6. 아직 별도로 검증해야 할 논문 기능

다음 항목은 E0에서 제거된 것이 아니라 modernized Odyssey에 다시 연결해야 하는 기능이다.

- 40 primitive + 183 compositional skill corpus
- Sentence Transformer description/query embedding
- top-5 기본·top-10 별도 profile의 semantic retrieval
- MineMA actor의 exact candidate 선택
- recursive prerequisite 실행
- planner–actor–critic feedback과 replanning
- 논문 benchmark의 task·prompt·성공 조건

Voyager의 curriculum, code generation/repair와 dynamic skill commit도 삭제하지 않는다. 공개 Odyssey 고정-library baseline과 분리해 `voyager-lifelong`과 `odyssey-full`에서 보존한다.

## 7. 현재 사용하는 문서

- 연구 방향과 시스템: [`MineSkynet_blueprint.md`](./MineSkynet_blueprint.md)
- Odyssey 현대화 완료 조건: [`modernization_milestone.md`](./milestone_goal/modernization_milestone.md)
- 논문–코드–dependency 근거: [`paper_code_dependency_map.md`](./paper_code_dependency_map.md)
- 설치·실행 명령: [`research/README.md`](../README.md)

과거 E0~E4 번호는 오류 기록을 찾기 위한 역사적 이름으로만 유지한다. 이후 완료 판단은 component 이름과 실제 증거 범위로 기록한다.
