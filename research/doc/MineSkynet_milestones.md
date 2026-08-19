# MineSkynet 연구 마일스톤

최종 갱신: 2026-08-20
상세 설계는 [`MineSkynet_blueprint.md`](./MineSkynet_blueprint.md), 실행 판단은 [`MVP_report.md`](./MVP_report.md)를 기준으로 한다.

상태 표기: `[x]` 완료, `[~]` 진행 중, `[ ]` 미착수, `[!]` 차단·판단 필요.

## 연구 마일스톤

- [~] [M0 — 실행 계층 고정](./milestone_goal/M0.md): 정상·failure-path·새 server·20회 증거 검증을 통과했고 commit/tag 고정만 남았다.
- [ ] [M0.5 — 최소 controller](./milestone_goal/M0_5.md): deterministic stub, strict registry와 일반 verifier로 E1 전체 경로를 검증한다.
- [ ] [M1 — 실제 actor 검증](./milestone_goal/M1.md): fixed candidate 조건에서 base actor를 먼저 평가하고 과거 LoRA 결과를 통제 비교한다.
- [ ] [M1.5 — Odyssey baseline 복원](./milestone_goal/M1_5.md): 고정 223-skill corpus, Sentence Transformer top-5 retrieval와 planner–actor–critic을 복원한다.
- [ ] [M1.75 — Voyager lifelong·Odyssey Full](./milestone_goal/M1_75.md): 능동 skill 생성·수정·검증·versioned commit·재사용 lifecycle을 격리 복원한다.
- [ ] [M2 — 세 물리 노드 연결](./milestone_goal/M2.md): RTX 3090·GTX 1050 Ti·Raspberry Pi가 독립 bot을 제어하게 한다.
- [ ] [M3 — Atomic capability calibration](./milestone_goal/M3.md): 장치·모델별 성공률, 지연, 에너지와 메모리 profile을 만든다.
- [ ] [M4 — Cloud planner와 State Manager](./milestone_goal/M4.md): task DAG, 공유 상태, retrieval과 실패 재계획을 중앙 계층에 구현한다.
- [ ] [M5 — Capability-aware allocation](./milestone_goal/M5.md): capability·이동·동기화·실패 비용을 반영한 배정 정책을 baseline과 비교한다.
- [ ] [M6 — 통합 벤치마크](./milestone_goal/M6.md): 성공률·makespan·비용·에너지·통신·orchestration overhead를 반복 측정한다.
- [ ] [M7 — 논문·공개 패키지](./milestone_goal/M7.md): 주장과 결과를 연결하고 설치·재현 자료와 한계를 정리한다.

## 검증 Gate

- [~] [E0 — `e0-executor`](./milestone_goal/E0.md): 구현과 정상·실패 회귀는 모두 통과했으며 성공 commit/tag 고정만 남았다.
- [ ] [E1 — `e1-stub`](./milestone_goal/E1.md): controller → stub actor → registry → executor → verifier를 두 task에서 각각 10/10 검증한다.
- [ ] [E2 — `e2-actor-fixed`](./milestone_goal/E2.md): 실제 actor의 fixed-candidate 선택 정확도와 Minecraft 성공률을 분리 측정한다.
- [ ] [E3 — Odyssey retrieval·legacy](./milestone_goal/E3.md): 논문 조건의 semantic retrieval와 고정-library Odyssey baseline을 재현한다.
- [ ] [E4 — lifelong·Full](./milestone_goal/E4.md): dynamic skill lifecycle과 static Odyssey baseline을 분리해 검증한다.

현재 우선순위는 E0 변경 범위 검토·commit/tag 고정 → E1 진입이다. 운영 명령은 [`research/README.md`](../README.md), 2026-08-20 E0 실행 증거는 [`E0_test_evidence_2026-08-20.md`](./E0_test_evidence_2026-08-20.md)에 둔다.
