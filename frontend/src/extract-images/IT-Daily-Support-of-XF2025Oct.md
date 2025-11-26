# IT Daily Support of XF2025Oct.pdf

---

**Author**: Microsoft® Word 2010

**Title**: No description found.

**Published**: 2025/11/25 下午9:25:01

**Pages**: 5

**Images**: 5

**Word Count**: 580

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

![Figure Figure from page 2 from page 2](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page2_img0_1764077103627.png "Figure from page 2")
![Figure  Follow below image for visual step-by-step instructions on downloading the from page 2](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page2_img1_1764077103643.jpg " Follow below image for visual step-by-step instructions on downloading the")

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

![Figure Figure from page 3 from page 3](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page3_img0_1764077103699.png "Figure from page 3")

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

![Figure Figure from page 4 from page 4](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page4_img0_1764077103735.png "Figure from page 4")
![Figure Figure from page 4 from page 4](src/extract-images/IT-Daily-Support-of-XF2025Oct.pdf_page4_img1_1764077103761.png "Figure from page 4")

2.2.4 Product line Scheduling(For Feifei Chou only) 
Directory Path: 
https://appprod.inteplast.com/appProduction/XF/Scheduling/ 
Installation Instructions:  
Use the same procedure as described in the Production Line Applications 
installation section.

---

## Image References

| Page | Image | Caption | Dimensions | Format |
|------|-------|---------|------------|--------|
| 2 | 1 | Figure from page 2 | 1491x731 | png |
| 2 | 2 |  Follow below image for visual step-by-step instructions on downloading the | 1232x290 | jpg |
| 3 | 3 | Figure from page 3 | 836x132 | png |
| 4 | 4 | Figure from page 4 | 1661x593 | png |
| 4 | 5 | Figure from page 4 | 1202x626 | png |
