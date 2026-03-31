# Mediscan
## Problem statement
Healthcare systems operate on fragmented and heterogeneous medical records, including handwritten prescriptions, printed reports, and unstructured digital documents. This fragmentation results in poor accessibility of patient information, increased risk of data inconsistency, and delays in clinical decision-making. Existing approaches rely heavily on manual digitization methods such as scanning and data entry, which are time-consuming, error-prone, and incapable of extracting structured and usable medical data efficiently. Consequently, there is a critical need for an intelligent and automated system that can transform unstructured medical records into structured, unified, and accessible patient health information within a centralized framework.

## Architecture diagram <!-- set width = 800, height = 1200 -->
<img width="800" height="1200" alt="image" src="https://github.com/user-attachments/assets/0a8931af-ad28-4511-b72e-7ff8c183ab00" />




## Raspberry Pi 
**hostname** aka machine name is `dharun-rasbpi`.
**macOS** users can connect directly using username@hostname `dharunmr@dharun-rasbpi.local`.

Unfortunately windows users using **WSL** cannot use the above step, but there is an alternative option for that.

**Windows WSL** users first need to get the **IP address** from the *macOS users* by `hostname -I` commmand to get the ip address.

Then `windows users` need to open the **cmd prompt** and then `ping 10.x.x.x` to ensure it is working, then
can connect using username@hostIP `dharunmr@10.x.x.x`

## Steps to connect to Raspberry Pi via SSH
### Generate the SSH key pair
```
ssh-keygen -t ed25519 -C "yourname"
```
Enter your name to save the keys in the format of `yourname`, `yourname.pub`. Here `yourname` is your private key that should reside in your machine, `yourname.pub` is your public key that you should copy to the **Raspberry Pi**

### Copy your SSH public key and connect to the Raspberry Pi

macOS users:
```
ssh-copy-id -i yourname.pub dharunmr@dharun-rasbpi.local
```
```
ssh -i ~/.ssh/yourname dharunmr@dharun.raspbi.local
```
WSL users:
```
ssh-copy-id -i yourname.pub dharunmr@10.x.x.x
```
```
ssh -i ~/.ssh/yourname dharunmr@10.x.x.x
```

