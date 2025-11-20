# IT Daily Support of XF2025Oct.pdf

---

**Author**: Microsoft® Word 2010

**Title**: No description found.

**Published**: 2025/11/20 下午2:50:21

**Pages**: 37

**Images**: 55

**Word Count**: 2033

---

IT Support of XF  
2025 Oct  
1. Production-Line Application  
1.1 Installation Guidelines 
1.1.1 Identify your production area in the Application Reference Table below. 
1.1.2 Click the appropriate Installation Link. 
1.1.3 Download and run the setup.exe installer. 
1.1.4 Follow on-screen prompts to complete installation. 
1.1.5 Verify printer connection using the static IP listed for your area. 
1.2 Important Configuration Notes 
1.2.1 Do not manually add printers. 
1.2.2 All label printers use static IP addresses. 
1.2.3 Only update IP if printer hardware has been replaced. 
 
1.3 Application Reference Table 
Section Area Label Printer 
IP （Large） 
Label Printer 
IP  (Small) 
Installation Link 
Coextrusion COEX 172.17.30.91  
 appprod.inteplast.com - 
/appProduction/XF/CoExtrusion/  
 
Spiral-Cut Spiral-Cut 172.17.30.92  
 appprod.inteplast.com - 
/appProduction/XF/SpiralCut/  
 
Stretch-
Lamination 
Stretch-
Lamination 
172.17.30.93  
 appprod.inteplast.com - 
/appProduction/XF/StretchLamination/  
 
G-Lamination G-mination 172.17.30.94  
 appprod.inteplast.com - 
/appProduction/XF/GLaminator/  
 
Slitting HA 12&13 172.17.30.167 172.17.31.65 
 appprod.inteplast.com - 
/appProduction/XF/Slitting/  
 
Slitting HA 14 172.17.30.97 172.17.30.96 
 appprod.inteplast.com - 
/appProduction/XF/Slitting/  
 
Slitting HA 15 172.17.30.98 172.17.30.98 
 appprod.inteplast.com - 
/appProduction/XF/Slitting/  
 
Shipping Shipping 172.17.30.55  
appprod.inteplast.com - 
/appProduction/XF/Schedule/  
Edge-
Lamination 
Edge-
Lamination 
172.17.30.103 172.17.30.102 
appprod.inteplast.com - 
/appProduction/XF/EdgeLamination/  
Printing & VF Printing & 
VF 
172.17.30.101 172.17.30.100 
appprod.inteplast.com - 
/appProduction/XF/Printing/1.4 Installation Visual Guide  
Directory Path: 
        \\ https://appprod.inteplast.com/appProduction/XF/   
Steps: 
 Select The correct application folder 
 Follow below image for visual step-by-step instructions on downloading the 
application setup.exe file 
 
 Follow below image for visual step-by-step instructions on running the 
application setup.exe file 
 
 
 
2. IT Support for Office  
 
2.1 Access Permission of XF’s NAS 
IT only have access to the “Software” folder on the XF Network Attached Storage (NAS). 
Directory Path of XF’s NAS: 
NAS Path:  \\172.17.25.100\  
Username: cyber  
Password:  softwareteam

![Figure Figure from page 2 from page 2](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page2_img0_1763621423472.png "Figure from page 2")
![Figure  Follow below image for visual step-by-step instructions on downloading the from page 2](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page2_img1_1763621423481.jpg " Follow below image for visual step-by-step instructions on downloading the")

2.2 New Computer Setup 
When setting up a new computer in the XF Office, complete the following installations:  
 
2.2.1 Install the Anti-Virus 
Directory Path: 
        \\172.17.25.100\Software\Cyber\WPJK Anti-Virus\  
Steps: 
 Navigate to the path above. 
 Locate the file cmd.bat. 
 Run the cmd.bat batch file to install the antivirus software. 
 
 
 
2.2.2 Install the steps of new AS400 
Directory Path: 
\\172.17.25.100\Software\Cyber\AS400（New Version）\ 
Installation Steps:  
1) Run jre1.8.0_26164 (Java Runtime) located in the directory 
above.  
2) Navigate to the folder:  
IBM ACS Client → Files → Windows_Application.  
3) Choose the correct installer based on your system architecture:  
For 32-bit systems: install_acs_32_allusers  
 For 64-bit systems: install_acs_64_allusers

![Figure Figure from page 3 from page 3](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page3_img0_1763621423499.png "Figure from page 3")

4) After install the AS400, please copy the “FPCTX.hod” icon and paste to the user’s 
desktop. 
Directory Path: 
\\172.17.25.100\Software\Cyber\AS400（New Version）\IBM ACS 
Client\Files\FPCTX.hod 
Steps： 
please copy the “FPCTX.hod” icon and paste to the user’s desktop. 
 
 
2.2.3 Plant Management for Supervisor 
Directory Path: 
https://appprod.inteplast.com - /appProduction/XF/PlantMgt/ 
Installation Instructions: 
Follow the same installation steps as outlined for the Production Line Applications.

![Figure Figure from page 4 from page 4](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page4_img0_1763621423541.png "Figure from page 4")
![Figure Figure from page 4 from page 4](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page4_img1_1763621423585.png "Figure from page 4")

2.2.4 Product line Scheduling(For Feifei Chou only) 
Directory Path: 
https://appprod.inteplast.com/appProduction/XF/Scheduling/ 
Installation Instructions:  
Use the same procedure as described in the Production Line Applications 
installation section. 
 
3. Install and connect the Kyocera printer for office user 
3.1 Download and install the printer’s driver and connect the printer from the Kyocera web site. 
https://youtu.be/F_pz6BIsRXY 
3.1.1 If you are first time to connect the Kyocera printer, you should be downloaded the 
driver from Kyocera web site. 
https://www.kyoceradocumentsolutions.com/download/index_en.html?r=0 
 
Select your country first.

![Figure Figure from page 5 from page 5](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page5_img0_1763621423614.png "Figure from page 5")

3.1.2 Check the Brand/Model/IP address and Hostname 
 
Brand:

![Figure Figure from page 6 from page 6](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page6_img0_1763621423617.jpg "Figure from page 6")
![Figure Figure from page 6 from page 6](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page6_img1_1763621423629.jpg "Figure from page 6")

Model: 
 
 
IP address and Hostname:

![Figure Figure from page 7 from page 7](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page7_img0_1763621423632.jpg "Figure from page 7")
![Figure Figure from page 7 from page 7](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page7_img1_1763621423635.jpg "Figure from page 7")
![Figure Figure from page 7 from page 7](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page7_img2_1763621423638.jpg "Figure from page 7")

3.1.3 Select the model from web site. 
 
3.1.4 Download the driver

![Figure Figure from page 8 from page 8](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page8_img0_1763621423640.jpg "Figure from page 8")
![Figure Figure from page 8 from page 8](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page8_img1_1763621423643.jpg "Figure from page 8")

3.1.5 Check the download file 
 
3.1.6 Right click to Extract all the zip file

![Figure Figure from page 9 from page 9](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page9_img0_1763621423663.png "Figure from page 9")
![Figure Figure from page 9 from page 9](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page9_img1_1763621423678.png "Figure from page 9")

3.1.7 Select the folder to extract

![Figure Figure from page 10 from page 10](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page10_img0_1763621423709.png "Figure from page 10")

3.1.8 Check the extract file and open the folder 
 
3.1.9 Double click the “Setup” file

![Figure Figure from page 11 from page 11](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page11_img0_1763621423725.png "Figure from page 11")
![Figure Figure from page 11 from page 11](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page11_img1_1763621423743.png "Figure from page 11")

3.1.10 Select the “Custom Install”

![Figure Figure from page 12 from page 12](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page12_img0_1763621423767.png "Figure from page 12")
![Figure Figure from page 12 from page 12](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page12_img1_1763621423799.png "Figure from page 12")

3.1.11 Find the printer and select it, then click the blue “arrow” 
 
3.1.12 Check if the printer is correctly displayed on the “product to install”, select the “KX 
DRIVER” and click the black arrow

![Figure Figure from page 13 from page 13](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page13_img0_1763621423801.jpg "Figure from page 13")

3.1.13 Double check the products to install, then click the install button

![Figure Figure from page 14 from page 14](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page14_img0_1763621423803.jpg "Figure from page 14")

3.1.14 The printer driver will be installed

![Figure Figure from page 15 from page 15](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page15_img0_1763621423808.jpg "Figure from page 15")

3.1.15 Printer the test page and click the “Finish” button

![Figure Figure from page 16 from page 16](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page16_img0_1763621423824.png "Figure from page 16")

3.1.16 Close the setup application

![Figure Figure from page 17 from page 17](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page17_img0_1763621423836.png "Figure from page 17")

3.1.17 The printer should be installed. Please check the “Printers& scanners” 
 
3.1.18 Print the test page and click the “Finish” button.

![Figure Figure from page 18 from page 18](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page18_img0_1763621423873.png "Figure from page 18")
![Figure Figure from page 18 from page 18](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page18_img1_1763621423900.png "Figure from page 18")

3.2 Connect/reconnect the printer from the network 
https://youtu.be/hCYFL-8s914 
3.2.1 Find the printer you want to connect to

![Figure Figure from page 19 from page 19](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page19_img0_1763621423915.png "Figure from page 19")

3.2.2 Check the Brand/Model/IP address and Hostname 
 
Brand:

![Figure Figure from page 20 from page 20](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page20_img0_1763621423924.jpg "Figure from page 20")
![Figure Figure from page 20 from page 20](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page20_img1_1763621423929.jpg "Figure from page 20")

Model: 
 
IP address and Hostname:

![Figure Figure from page 21 from page 21](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page21_img0_1763621423929.jpg "Figure from page 21")
![Figure Figure from page 21 from page 21](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page21_img1_1763621423932.jpg "Figure from page 21")

3.2.3 Go to start menu, open the settings from your computer 
 
3.2.4 Open the “Bluetooth & devices”

![Figure Figure from page 22 from page 22](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page22_img0_1763621423932.jpg "Figure from page 22")
![Figure Figure from page 22 from page 22](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page22_img1_1763621423935.jpg "Figure from page 22")

3.2.5 Then click the “Printers & scanners” to open the printer settings. 
 
3.2.6 Please click the “Add device” button

![Figure Figure from page 23 from page 23](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page23_img0_1763621423936.jpg "Figure from page 23")
![Figure Figure from page 23 from page 23](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page23_img1_1763621423960.png "Figure from page 23")

3.2.7 The computer will automatically detect all printers in your network segment 
 
3.2.8 Please find the printer from printer list

![Figure Figure from page 24 from page 24](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page24_img0_1763621423981.png "Figure from page 24")
![Figure Figure from page 24 from page 24](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page24_img1_1763621424011.png "Figure from page 24")

3.2.9 Find the Brand/Model and Hostname in the printer list 
 
3.2.10 If you find the correct printer in the printer list, click the “Add device” button 
 
3.2.11 If not, please click the “Add manually” to use the IP address to add printer

![Figure Figure from page 25 from page 25](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page25_img0_1763621424034.png "Figure from page 25")
![Figure Figure from page 25 from page 25](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page25_img1_1763621424048.png "Figure from page 25")
![Figure Figure from page 25 from page 25](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page25_img2_1763621424063.png "Figure from page 25")

3.2.12 If you click the “Add manually” button, another window will pop out(please see 
below picture) 
Please select the “Add a printer using an IP address or hostname”, then click the 
“next” button. 
 
3.2.13 Please select the TCP/IP Device from the Device type

![Figure Figure from page 26 from page 26](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page26_img0_1763621424095.png "Figure from page 26")
![Figure Figure from page 26 from page 26](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page26_img1_1763621424149.png "Figure from page 26")

3.2.14 Please typing the IP address, then click the “next” button

![Figure Figure from page 27 from page 27](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page27_img0_1763621424163.png "Figure from page 27")

3.2.15 select the driver 
Brand:

![Figure Figure from page 28 from page 28](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page28_img0_1763621424176.png "Figure from page 28")

Model: 
 
3.2.16 Finished

![Figure Figure from page 29 from page 29](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page29_img0_1763621424191.png "Figure from page 29")
![Figure Figure from page 29 from page 29](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page29_img1_1763621424199.png "Figure from page 29")

3.2.17 If you need, you can click the “Print a test page”, then click the “Finish” button

![Figure Figure from page 30 from page 30](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page30_img0_1763621424213.png "Figure from page 30")

4. Setup the email account of copy machine. 
The copy machine’s IP is 172.17.24.80(please setup below account to setup the email function 
of the copy machine) 
Username: Service@wpjk.inteplast.com 
password:  Bom07544 
Port:       587 
Smtp:       smtp .office365.com 
 
5. WIFI information 
5.1 XF Office Wi-Fi Overview 
The following information applies to the Wi-Fi network for the XF Office. 
Parameter  Value  
Router Mode  AP mode  
IP Address 172.17.26.128 (DHCP enabled)  
Router Management URL  http://www.routerlogin.net/ 
SSID (Network Name)  NETGEAR94

![Figure Figure from page 31 from page 31](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page31_img0_1763621424233.png "Figure from page 31")

Wi-Fi Access Password  fuzzyviolin497  
 
5.2 XF Plant Wi-Fi Router Info 
The following information applies to the Wi-Fi network for the XF Plant area. 
 
 
6. XF plant topology map 
The network diagram connects key areas of the XF facility. Yellow lines represent fiber-optic 
links, and blue lines represent Ethernet connections. Please refer to the image below for the 
complete topology diagram. 
Step: 
•  Identify the fault symptoms 
Collect a description of the problem (inability to access the internet, high latency, failure 
to access specific websites, etc.) 
Identify the scope of impact (single unit/department/network-wide) 
Record the time, device, IP address, and error information (e.g., 
DNS_PROBE_FINISHED_BAD_CONFIG) 
   
• Physical layer and data link layer checks 
Checkpoint Action Expected Result 
Power Verify switch/router power status Restart or replace if unpowered 
Cabling Check port LED, ensure cables are secure Replace damaged cables 
Wi-Fi Verify SSID and signal strength Reconnect or move closer to AP 
 
• Network Layer Connectivity 
 Check Local IP and Gateway:（open The command prompt） 
 ipconfig /all 
 correct results：ping 172.17.24.1 
Correct  results： 
 
 Test External Connectivity: 
ping 8.8.8.8 
correct results：

![Figure Figure from page 33 from page 33](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page33_img0_1763621424262.png "Figure from page 33")
![Figure Figure from page 33 from page 33](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page33_img1_1763621424277.png "Figure from page 33")

 DNS Layer Verification 
nslookup AS400.inteplast.com 
correct results： 
 
Observation Interpretation 
Correct IP returned（172.18.16.21） DNS normal 
Timeout / no response DNS server issue or misconfiguration 
Incorrect IP Possible DNS hijack; check hosts file or security policy 
 
 Application Layer Testing 
Service Health Check:（command） 
curl -I https://wpjk.inteplast.com 
→If correct, you will see below infomation 
HTTP/1.1 200 OK 
Server: nginx/1.28.0 
Date: Thu, 13 Nov 2025 21:06:43 GMT 
Content-Type: text/html 
Content-Length: 525 
Last-Modified: Thu, 28 Aug 2025 00:55:29 GMT 
Connection: keep-alive 
ETag: "68afa901-20d" 
Accept-Ranges: bytes→ If 5xx errors, likely an application or backend issue. 
 
• Finish Check of the connection, please open the application again. 
 
XF network topology:

![Figure Figure from page 34 from page 34](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page34_img0_1763621424287.png "Figure from page 34")
![Figure Figure from page 34 from page 34](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page34_img1_1763621424302.png "Figure from page 34")

XF network map：

![Figure Figure from page 35 from page 35](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page35_img0_1763621424325.png "Figure from page 35")

7. Fixed IP of XF 
172.17.24.80 copy machine in the office 
172.17.25.100 NAS in the maintenance office 
172.17.27.10 QC query server 
 
 
 
8. Q&A 
8.1 User couldn’t login to the AS400 
 ping to the AS400 server 
call or email to the NJ IT to help us. 
 show the message on the AS400, “incorrect password or user does not exists.” 
Let user to wait 15 mins, then try it again. 
 
8.2 What is the DNS server? 
172.17.8.25 
172.18.16.53 
172.19.254.52 
 
8.3 What is the Gateway of XF?

![Figure Figure from page 36 from page 36](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page36_img0_1763621424327.jpg "Figure from page 36")

172.17.24.1 
 
8.4 What is the netmask of XF? 
255.255.248.0 
 
8.5   
9.

---

## Image References

| Page | Image | Caption | Dimensions | Format |
|------|-------|---------|------------|--------|
| 2 | 1 | Figure from page 2 | 1491x731 | png |
| 2 | 2 |  Follow below image for visual step-by-step instructions on downloading the | 1232x290 | jpg |
| 3 | 3 | Figure from page 3 | 836x132 | png |
| 4 | 4 | Figure from page 4 | 1661x593 | png |
| 4 | 5 | Figure from page 4 | 1202x626 | png |
| 5 | 6 | Figure from page 5 | 1299x659 | png |
| 6 | 7 | Figure from page 6 | 1138x617 | jpg |
| 6 | 8 | Figure from page 6 | 506x412 | jpg |
| 7 | 9 | Figure from page 7 | 1109x562 | jpg |
| 7 | 10 | Figure from page 7 | 1108x560 | jpg |
| 7 | 11 | Figure from page 7 | 512x243 | jpg |
| 8 | 12 | Figure from page 8 | 497x406 | jpg |
| 8 | 13 | Figure from page 8 | 1207x617 | jpg |
| 9 | 14 | Figure from page 9 | 1204x617 | png |
| 9 | 15 | Figure from page 9 | 1299x278 | png |
| 10 | 16 | Figure from page 10 | 1146x750 | png |
| 11 | 17 | Figure from page 11 | 724x600 | png |
| 11 | 18 | Figure from page 11 | 1005x155 | png |
| 12 | 19 | Figure from page 12 | 1139x820 | png |
| 12 | 20 | Figure from page 12 | 1030x839 | png |
| 13 | 21 | Figure from page 13 | 1030x839 | jpg |
| 14 | 22 | Figure from page 14 | 1030x839 | jpg |
| 15 | 23 | Figure from page 15 | 1030x839 | jpg |
| 16 | 24 | Figure from page 16 | 704x556 | png |
| 17 | 25 | Figure from page 17 | 704x556 | png |
| 18 | 26 | Figure from page 18 | 1030x839 | png |
| 18 | 27 | Figure from page 18 | 1194x634 | png |
| 19 | 28 | Figure from page 19 | 725x601 | png |
| 20 | 29 | Figure from page 20 | 500x666 | jpg |
| 20 | 30 | Figure from page 20 | 506x412 | jpg |
| 21 | 31 | Figure from page 21 | 1109x562 | jpg |
| 21 | 32 | Figure from page 21 | 1108x560 | jpg |
| 22 | 33 | Figure from page 22 | 497x406 | jpg |
| 22 | 34 | Figure from page 22 | 1074x994 | jpg |
| 23 | 35 | Figure from page 23 | 1168x620 | jpg |
| 23 | 36 | Figure from page 23 | 1177x625 | png |
| 24 | 37 | Figure from page 24 | 1183x628 | png |
| 24 | 38 | Figure from page 24 | 1188x631 | png |
| 25 | 39 | Figure from page 25 | 944x636 | png |
| 25 | 40 | Figure from page 25 | 1269x81 | png |
| 25 | 41 | Figure from page 25 | 1255x76 | png |
| 26 | 42 | Figure from page 26 | 1291x860 | png |
| 26 | 43 | Figure from page 26 | 1317x890 | png |
| 27 | 44 | Figure from page 27 | 725x601 | png |
| 28 | 45 | Figure from page 28 | 725x601 | png |
| 29 | 46 | Figure from page 29 | 725x600 | png |
| 29 | 47 | Figure from page 29 | 635x149 | png |
| 30 | 48 | Figure from page 30 | 725x600 | png |
| 31 | 49 | Figure from page 31 | 725x629 | png |
| 33 | 50 | Figure from page 33 | 965x610 | png |
| 33 | 51 | Figure from page 33 | 686x289 | png |
| 34 | 52 | Figure from page 34 | 691x285 | png |
| 34 | 53 | Figure from page 34 | 690x160 | png |
| 35 | 54 | Figure from page 35 | 895x661 | png |
| 36 | 55 | Figure from page 36 | 1298x837 | jpg |
