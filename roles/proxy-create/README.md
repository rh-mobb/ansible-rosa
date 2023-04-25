To recreate the squid certs

```
openssl req -new -newkey rsa:2048 -sha256 -days 365 \
  -nodes -x509 -extensions v3_ca -keyout files/squid-ca-key.pem \
  -out files/squid-ca-cert.pem

cat files/squid-ca-cert.pem files/squid-ca-key.pem > files/squid-ca-cert-key.pem


```
