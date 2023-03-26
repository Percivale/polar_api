# Polar Api 
## DETTE GJØRES EN GANG PER BRUKER 
* Åpne Anaconda navigator fra Windows start meny (eller søk etter anaconda i forstørrelsesglass)
* Bytt til kanal: myspss
* Launch Anaconda powershell
* bytt mappe : cd "\\ihelse.net\Forskning\hst\ID1321\polar_api_kode\polar_data"
* lag en ny mappe med navn deltagerID
* i Anaconda powershell: cd deltagerID ; cp ..\config.yml .\
* åpne https://admin.polaraccesslink.com/
 - http://localhost:5000/oauth2_callback as the authorization callback domain for this example
* Fill in your client id and secret in config.yml: (eksempel)
client_id: a06f49dxxxx
client_secret: 0137xxxx

* i Anaconda powershell: python ..\..\src\authorization.py
and navigate to: (erstatt CLIENT_ID med client_id i config.yml fila)
https://flow.polar.com/oauth2/authorization?response_type=code&client_id=CLIENT_ID
to link user account.
* hvis alt gikk bra så har fila config.yml følgende innhold (eksempel)
access_token: c5951xxx
client_id: a06f49xxx
client_secret: 01374axxx
user_id: 50xxxxx

## HENTING AV DATA 

* Åpne Anaconda navigator fra Windows start meny (eller søk etter anaconda i forstørrelsesglass)
* Bytt til kanal: myspss
* Launch Anaconda powershell
* bytt til mappe med brukerinformasjon (erstatt bruker_id med mappe navn til bruker, eks: 600X) : 
      cd "\\ihelse.net\Forskning\hst\ID1321\polar_api_kode\polar_data\bruker_id"
* i anaconda powershell:  python ..\..\src\AccessPolarFlow.py


