# Pareceres da primeira submissão (VII SIMECA)

Texto dos revisores, recebido em 2026-10-29, sobre o `artigo_modem.md` desta pasta.

## Revisor 1

O trabalho está dentro do escopo temático do evento, apresenta relevância acadêmica e traz um tema importante para estudo na área de telecomunicações. Considerando a importância do tema, senti falta de uma pesquisa mais aprofundada, com citação de mais autores/trabalhos sobre o tema. A escrita não está fluída, dificultando a leitura. Recomendo ajustar a forma como algumas partes do trabalho são escritas, há falta de coesão, ou uso de termos não técnicos em partes do trabalho, por exemplo, no resumo: "O meio acústico impõe condições severas" -> parece ser uma frase solta. "a amplitude que chega não é a que saiu" -> Utilizar termos mais técnicos, como emitida e recebida. Evitar o uso de conjugação de verbo na primeira pessoa. Outro exemplos: "O Bell 202 permanece em uso industrial" parece uma frase solta. "e Lopes e Aguiar (2001)" retirar o e inicial "Nesta bancada o som também não " qual bancada? "Os dados vão" Entre outros Ou seja, verifique o texto como um todo, de maneira que a leitura se torne mais fluída.

## Revisor 2

O trabalho apresenta uma proposta interessante e resultados experimentais coerentes com o que foi proposto. No entanto, há algumas inconsistências que precisam ser verificadas: - No quarto parágrafo da seção introdutória, a afirmação de que o "som viaja mais de 87.000 vezes mais devagar que a onda eletromagnética" deve ser revista (aproximadamente 875.000 vezes). - No quinto parágrafo da Seção 2.2, a afirmação de que "a decisão fica indiferente à amplitude" é um pouco exagerada. O que ocorre é que comparação relativa entre frequências reduz a sensibilidade a variações de ganho comum no enlace, mas a probabilidade de erro na decisão ainda é dependente da relação sinal-ruído (SNR). - Para um código Gray de 4 bits, todos os 15 pares de valores consecutivos possuem distância de Hamming igual a 1. Portanto, não seria possível receber códigos que diferem em um único bit em doze dos quinze pares.

## Como cada ponto é tratado na segunda versão

- Escrita, coesão, primeira pessoa: texto refeito do zero, em voz impessoal.
- Referências: duas a mais no máximo (ggwave e Lopes e Aguiar 2003), por falta de espaço.
- 87 mil: a razão é 3,0×10⁸ / 343 ≈ 8,7×10⁵. O número vinha de Putz *et al.* (2026); o texto novo dá a conta sem atribuí-la.
- Amplitude: a comparação entre frequências remove o ganho comum; a probabilidade de erro continua dependendo da SNR.
- Gray: o código põe o valor v no tom gray(v), o mapeamento inverso; três pares de tons vizinhos ficam a 2 bits. Correção em `modem.py` (valor = gray(tom)) antes da medição da Tabela 1.
