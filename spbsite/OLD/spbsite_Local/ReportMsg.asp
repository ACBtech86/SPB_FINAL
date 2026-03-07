<%@ Language=VBScript %>
<%OPTION EXPLICIT%>
<HTML>
  <HEAD>
    <TITLE>Form Report Mensagem Page</TITLE>
  </HEAD>
<BODY>
  <P align="center"><FONT face="verdana" size="3" color="navy">Mensagem SPB</FONT></P>
  <TABLE border="0" id=TABLE1>
<%
Dim strSelect ' As String
Dim strWork   ' As String
dim docElem
dim xmlnode
dim XmlDoc

Set XmlDoc = Server.CreateObject("microsoft.xmldom")

strSelect = Request.Form("select1")
Response.Write("<BR/> Report Msg!")
strWork = strSelect
XmlDoc.loadXML (strWork)
set docElem = XmlDoc.documentElement
set xmlnode = XmlDoc.selectNodes("SPBDOC")
strwork = xmlnode.nodeName()
'Response.Write("<BR/> Node:" & xmlnode.xml)
Response.Write("<BR/> Fim Mensagem Xml!")


%>
</td></TR>
</TABLE>
  </BODY>
</HTML>

