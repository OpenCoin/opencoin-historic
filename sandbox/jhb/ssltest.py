import ssl, socket, base64
cert = ssl.get_server_certificate(('secure.orange-vision.de',443))
file('cacert.pem','w').write(cert)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ss = ssl.wrap_socket(s,cert_reqs=ssl.CERT_OPTIONAL,ca_certs='cacert.pem')
ss.connect(('secure.orange-vision.de',443))
print base64.b64encode(ss.getpeercert(1))
