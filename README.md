# Polar Api 

Info om [autorisering](https://github.com/polarofficial/accesslink-example-python). Husk dette må gjøres før data blir synkronisert/samlet opp av klokka. 

Kort fortalt, kjør en gang per user for å autorisere
```
Terminal> python authorization.py
```
For å hente data
```
Terminal> python accesslink_example.py
```

Filen med koden jeg har skrevet ligger i accesslink_example.py. Funksjonen som henter data fra de forskjellige stedene (physical info, daily activity, exercise, sleep og nightly recharge) og lagrer hver av dem i en egen excel fil med brukerdefinert navn heter `get_available_data()`. Det blir ikke gjort noe særlig formatering her.

Funksjonen `get_dataframes()` gjør en del formattering. Den henter sleep data og gjør verdiene som er telt i sekunder om til timer og minutter (format: h:mm). I tillegg legger den til en kolonne med antall timer søvn totalt. Funksjonen prøver også å legge sammen all dataen i en dataframe, men det er ikke alt som fungerer. 

Funksjonen `format_excel()` gjør den endelige formateringen og henter de viktige kolonnene og gir dem riktig navn. Legger også til en kolonne index1, som er antall dager personen har hatt klokka. Funksjonen `index_col()` lager den kolonnen. 

Tror at `get_dataframes()` har mange kodesnutter som er nyttige til å renske og sette sammen flere små excel filer. 
