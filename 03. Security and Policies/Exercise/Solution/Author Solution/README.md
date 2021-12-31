# Create and register two Kubernetes uses – Ivan (ivan) and Mariana (mariana) who are part of the Gurus (gurus) group

Create the two users

```bash
useradd -m -c 'Ivan' -s /bin/bash ivan 
useradd -m -c 'Mariana' -s /bin/bash mariana
```

Prepare the subfolders for both users

```bash
mkdir -p /home/{ivan,mariana}/{.certs,.kube}
```

Create the private keys for both users

```bash
openssl genrsa -out /home/ivan/.certs/ivan.key 2048
openssl genrsa -out /home/mariana/.certs/mariana.key 2048
```

Create a certificate signing request (CSR) for every user

```bash
openssl req -new -key /home/ivan/.certs/ivan.key -out /home/ivan/.certs/ivan.csr -subj "/CN=ivan/O=gurus"
openssl req -new -key /home/mariana/.certs/mariana.key -out /home/mariana/.certs/mariana.csr -subj "/CN=mariana/O=gurus"
```

Sign both CSRs with the Kubernetes CA certificate

```bash
openssl x509 -req -in /home/ivan/.certs/ivan.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out /home/ivan/.certs/ivan.crt -days 365
openssl x509 -req -in /home/mariana/.certs/mariana.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out /home/mariana/.certs/mariana.crt -days 365
```

Create the credentials for the two users

```bash
kubectl config set-credentials ivan --client-certificate=/home/ivan/.certs/ivan.crt --client-key=/home/ivan/.certs/ivan.key
kubectl config set-credentials mariana --client-certificate=/home/mariana/.certs/mariana.crt --client-key=/home/mariana/.certs/mariana.key
```

Create the contexts for the two users

```bash
kubectl config set-context ivan-context --cluster=kubernetes --user=ivan
kubectl config set-context mariana-context --cluster=kubernetes --user=mariana
```

Create configuration file for **ivan** at ```/home/ivan/.kube/config``` with the following content:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXlNREV4TWpReU5Gb1hEVE14TVRFeE9ERXhNalF5TkZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTUdpClJKMHY3NEg5R3RRR3M2UVQ2Qzc3R1d0QXdXRmcxV0pGbFFaUU9rTmdzbU5LVzJNbHdOL01ydGZTYXlEU2ZJc0sKTjlzRjRGN3ZmYUFNQThhdVYxSTc0QVZZQTZ6aUxqc1NpNGhjeGhSUHJrSlRRSWVUVk1MUzVWaml5d0VnRTlCVwozOElmYVo3cjZBUXMwZ1Jlb3FXWGpkUDZzZFAyckZ2b1lzVE5oZFVodmVtenBEQXJ2ekpMRWtWSEhPc09Fa01OClo4WkZ5SFU2amM1YkUzRkVxaXpZdENVdHpxaENBYkhsQVVnMmN0cTJXbjl6ZGdGUUNKQXJPOWpJWVEwZFRjUngKYUV2UmlMSUZsTy91RHRuUkUydnEwdHF3cDduMzg0VlBmNXdQVndEY1ZGN0VZYk9BZUJJOHJsMmtsVGhlQm5nKwovT1NTbUhndjVhOGR5MkdvSXlNQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZNSE5tLzNYUzJSZnZ4MkwxMGhsWnpyVHpjTUFNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFBODJJNHBiR2VlUzNMNkFZRWlDanU3WnRTWERaOGJIMDFIZ20xWDBVQmNuOTU5aXZXYwphSHQyZVc4YzJWcFVGbVYzcFoxMXY1cWljVmk5NWlhUzFHT0VHdENpVUJHQ2FyWDZmdWdEWUdkQzlITmF6aEdiCndESkFMRU9Td0JLajZ1dTZxU2NlL0NlSmZhQjBsMzM2UjZaYU10eUNBU3RPSkYzMnBRVmxDZ21Xd3orQ0IvZmkKK0VySzUxamNtMGhVeVU3TVdhTlNEbHFHWDAyVzkxNjZuMUkvc1dxeGRpV0haMTBNZU1oMUJMWndDUFE5Mjc3dApFWCs5dkR5M0I5RnNzVVUzTHhCeldWd0ppTURNUGRYSklHUE9pYmlPUDZWcktrSHgrbzArSWk0OFBqTUVyME11Ckd5ZldUTG90SHdSWlZRMVVGTXhNY1RFK0Q5b21QMmxCc05FLwotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.71:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: ivan
  name: ivan-context
current-context: ivan-context
kind: Config
preferences: {}
users:
- name: ivan
  user:
    client-certificate: /home/ivan/.certs/ivan.crt
    client-key: /home/ivan/.certs/ivan.key
```

Create configuration file for **mariana** at ```/home/mariana/.kube/config``` with the following content:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXlNREV4TWpReU5Gb1hEVE14TVRFeE9ERXhNalF5TkZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTUdpClJKMHY3NEg5R3RRR3M2UVQ2Qzc3R1d0QXdXRmcxV0pGbFFaUU9rTmdzbU5LVzJNbHdOL01ydGZTYXlEU2ZJc0sKTjlzRjRGN3ZmYUFNQThhdVYxSTc0QVZZQTZ6aUxqc1NpNGhjeGhSUHJrSlRRSWVUVk1MUzVWaml5d0VnRTlCVwozOElmYVo3cjZBUXMwZ1Jlb3FXWGpkUDZzZFAyckZ2b1lzVE5oZFVodmVtenBEQXJ2ekpMRWtWSEhPc09Fa01OClo4WkZ5SFU2amM1YkUzRkVxaXpZdENVdHpxaENBYkhsQVVnMmN0cTJXbjl6ZGdGUUNKQXJPOWpJWVEwZFRjUngKYUV2UmlMSUZsTy91RHRuUkUydnEwdHF3cDduMzg0VlBmNXdQVndEY1ZGN0VZYk9BZUJJOHJsMmtsVGhlQm5nKwovT1NTbUhndjVhOGR5MkdvSXlNQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZNSE5tLzNYUzJSZnZ4MkwxMGhsWnpyVHpjTUFNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFBODJJNHBiR2VlUzNMNkFZRWlDanU3WnRTWERaOGJIMDFIZ20xWDBVQmNuOTU5aXZXYwphSHQyZVc4YzJWcFVGbVYzcFoxMXY1cWljVmk5NWlhUzFHT0VHdENpVUJHQ2FyWDZmdWdEWUdkQzlITmF6aEdiCndESkFMRU9Td0JLajZ1dTZxU2NlL0NlSmZhQjBsMzM2UjZaYU10eUNBU3RPSkYzMnBRVmxDZ21Xd3orQ0IvZmkKK0VySzUxamNtMGhVeVU3TVdhTlNEbHFHWDAyVzkxNjZuMUkvc1dxeGRpV0haMTBNZU1oMUJMWndDUFE5Mjc3dApFWCs5dkR5M0I5RnNzVVUzTHhCeldWd0ppTURNUGRYSklHUE9pYmlPUDZWcktrSHgrbzArSWk0OFBqTUVyME11Ckd5ZldUTG90SHdSWlZRMVVGTXhNY1RFK0Q5b21QMmxCc05FLwotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.71:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: mariana
  name: mariana-context
current-context: mariana-context
kind: Config
preferences: {}
users:
- name: mariana
  user:
    client-certificate: /home/mariana/.certs/mariana.crt
    client-key: /home/mariana/.certs/mariana.key
```
