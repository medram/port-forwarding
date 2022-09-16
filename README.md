# port-forwarding
Port forwarding using Python, it's great and useful for incomming forwarding connections to SSH or VPN (or even any back-end service)

## Usage:
```bash
python3 port_forwarding.py --server 9090 --target 127.0.0.1:22
```
The above command will start a server listening on 9090, and forwards all the incomming connections to target/destination<br> 
which is SSH server (127.0.0.1:22) in this case.


## License:
MIT License.

