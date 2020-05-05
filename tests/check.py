import requests

url = "https://10.182.50.117/mangle-services/rest/api/v1/endpoints/credentials/k8s?id=scdc1-staging-trace-it-now&name=scdc1-staging-trace-it-now"

payload = {}
files = [
  ('kubeConfig', open('/Users/bverma/Downloads/scdc1-staging-trace-it-now.yaml','rb'))
]
headers = {
  'Authorization': 'Basic YWRtaW5AbWFuZ2xlLmxvY2FsOmFkbWlu',
  'Cookie': 'JSESSIONID=DDA2982830A78998FDEEB4D2976E2ED4'
}

response = requests.request("POST", url, headers=headers, files = files, verify=False)

print(response.text.encode('utf8'))