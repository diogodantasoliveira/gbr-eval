# Princípios do Eval — Regras para Claude Code neste projeto

## Nunca gerar golden sets automaticamente
Golden sets são anotados por humano (CLO). Claude pode SUGERIR campos esperados, mas NUNCA pode criar um golden set e declarar como "validado".

## Graders devem ser funções puras
Todo grader determinístico implementa o Protocol:
```python
class Grader(Protocol):
    def grade(self, output: dict, expected: dict, spec: GraderSpec) -> GraderResult: ...
```
Sem side effects, sem estado, sem I/O. Exceção única: LLM-judge (documentada).

## Zero tautologia
Nunca comparar output consigo mesmo. Se um teste precisa de expected, o expected vem de um golden set real, não de um mock gerado.

## Separar o que mede do que decide
Graders medem. Thresholds decidem. Nunca hardcodar threshold dentro de um grader — receber como config.

## Schema first
Definir o schema Pydantic antes de implementar. Se o schema não existe, a feature não existe.
