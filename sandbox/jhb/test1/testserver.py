import socket

HOST = '127.0.0.1'    # The remote host
PORT = 12008              # The same port as used by the server


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind((HOST, PORT))
s.listen(1)

i = 0
while 1:
    i += 1
    print i
    try:
        data = conn.recv(1024)
    except:
        conn, addr = s.accept()
        data = conn.recv(1024)
    data  = data.replace('\r','')
    if not data:
        conn.close()
        conn, addr = s.accept()
    else:
        print repr(data)
        conn.send('["Receipt",null]')
conn.close()


