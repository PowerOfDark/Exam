### Instalacja

Wymagania:

* Python 3.7.x
* platforma Linux/Windows/Mac x64

Zacznij od sklonowania tego repozytorium:
```bash
git clone https://github.com/PowerOfDark/Exam && cd Exam
```

Przed następnym krokiem zalecane jest stworzenia środowiska *virtualenv*.

Zainstaluj wymagane pakiety:

```bash
python3 -m pip install --upgrade --user pip setuptools
pip install -r requirements.txt
```

## Pierwsze kroki

Głównym plikiem konfiguracyjnym będzie baza pytań i odpowiedzi. 
Rozpocznij od wygenerowania nowej bazy.

```bash
$ ./main.py create-problem-set
```

Jeżeli nie dostarczysz niezbędnych parametrów do polecenia, zostaniesz interaktywnie poproszony o ich podanie.

Nasz wygenerowany 'problem set' wygląda tak:

```yaml
uuid: 541626a0-1528-453f-888b-40ca42e67793
title: My problem set
question_defaults: # Parametry domyślne podczas tworzenia pytania
# można edytować poleceniem 'set-defaults' lub manualnie.
  id: ''  # unikalne, krótkie ID pytania
  text: ''  # treść pytania
  num_answers: 4  # liczba losowanych odpowiedzi
  num_correct_answers: 1  # liczba losowanych poprawnych odpowiedzi
  is_multiple_choice: false  # czy jest wielokrotnego wyboru
  likelihood: 1	 # prawdopodobieństwo wylosowania
  points: 1  # maksymalna liczba punktów
  grader: binary  # typ oceniania (graders.py)
# 'binary' - 0 lub maks. gdy wszystko dobrze
# 'linear' - proporcjonalnie do liczby dobrych
```



W każdej chwili możesz wykonać ``./main.py --help`` aby dostać listę poleceń 
lub ``./main.py COMMAND --help`` jeżeli potrzebujesz szczegółów polecenia.

```bash
$ ./main.py add-question --help
Usage: main.py add-question [OPTIONS]

  Adds a question to the problem set

Options:
  --id TEXT
  -t, --text TEXT
  -a, --num-answers INTEGER
  -c, --num-correct-answers INTEGER
  -p, --points INTEGER
  -g, --grader [binary|linear]
  -l, --likelihood INTEGER
  -m, --is-multiple-choice BOOLEAN
  --help                          Show this message and exit.
```



### Tworzenie pytań

Wykorzystując powyższe polecenie, dodajmy pytanie:

```bash
$ ./main.py --add-question -t "2+2=" -a 2 -c 1 --id easy1
```

Oczywiście otrzymamy błąd, ponieważ nie podaliśmy ścieżki do naszej bazy pytań.
Jedna z opcji to podanie ``--problem-set`` (lub ``-s``) w każdym poleceniu; druga to dodanie zmiennej środowiskowej:

```bash
$ export EXAM_PROBLEM_SET=problems.yml;
```

Po dodaniu naszego pytania, dodajmy odpowiedzi:

```bash
$ ./main.py add-answer -q easy1 --text "4" --correct true
$ ./main.py add-answer -q easy1 --text "3"
$ ./main.py list-questions
easy1: 2+2=
        1: [+] 4
        2: [-] 3
Processed 1 question(s)
```

To samo można osiągnąć manualnie modyfikując plik z bazą pytań:

```yaml
...
questions:
  q1:
    text: 'The expression `2^2^3` is equal to'
    is_multiple_choice: yes
    num_correct_answers: 2
    points: 4
    answers:
      - text: '2^8'     # id będzie dodane automatycznie
        is_correct: yes
      - text: '256'
        is_correct: yes
      - text: '0x100'
        is_correct: yes
      - text: '64'
      - text: '2^4'
      - text: '223'
    grader: 'linear'
...
```

Warto wspomnieć, że w wierszu poleceń nie istnieje opcja usunięcia pytania (żeby nie popsuć wcześniej generowanych sprawdzianów) -- zalecany sposób na pozbycie się pytania/odpowiedzi to ustawienie ``likelihood: 0``

### Sprawdziany

Sprawdzian to lista pytań i odpowiedzi (bez informacji o poprawności), którą można wygenerować ze zbioru pytań.

```bash
$ ./main.py -s ./examples/problems.yml gen-exam -n 10 -p exam.yml -t Sprawdzian -d Powodzenia!
```

Następnie sprawdzian można uzupełnić w interfejsie graficznym.

```bash
$ ./main.py open-exam exam.yml
```

Jeżeli podasz w poleceniu zbiór zadań, po wypełnieniu (i zapisaniu) sprawdzian zostanie oceniony.

```bash
$ ./main.py -s ./examples/problems.yml open-exam exam.yml
```



Wypełnione sprawdziany można przeglądać pojedynczo (tym samym poleceniem), albo wygenerować podsumowanie dla większej ilości:

```bash
$ ./main.py -s ./examples/problems.yml grade-exams ./examples/results -p
Per-user score stats:
1. Foo Baz: 21.0 / 21.0 (100.0%)
2. Foo Bar: 20.0 / 21.0 (95.2%)
3. Przemysław Rozwałka: 9.0 / 21.0 (42.9%)

Number of participants: 3
Mean score: 16.7 / 21.0 (79.4%)
Median score: 20.0 / 21.0 (95.2%)
```

Dodatkowo przełącznik ``-p`` wyświetli histogram wyników. Możliwe jest również podsumowanie punktów wg. pytań (``-q``)