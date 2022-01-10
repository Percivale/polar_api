import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.get('https://www.polaraccesslink.com/v3/users/50463526/activity-transactions/{transaction-id}/activities/{activity-id}/zone-samples', params={

}, headers = headers)

print( r.json())