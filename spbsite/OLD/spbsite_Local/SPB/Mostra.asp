<%@ Language=VBScript %>
<%OPTION EXPLICIT%>
<HTML>
  <HEAD>
    <TITLE>Mostra  Mensagem SPB</TITLE>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<LINK REL="stylesheet" TYPE="text/css" HREF="cidadespb.css" TITLE="formal">
</head>
<body bgcolor="#FFFFFF" text="#000000">
<!-- #INCLUDE file="connect.asp" -->
<%
Dim strqual 		' As String
Dim strXML    		' AS String
Dim strSql   		' As String
Dim objConnection 	' AS Object
Dim RS       		' AS Object  
	Set objConnection = CreateObject("adodb.connection")
	objConnection.Open strDBConnection
	strqual = Request.QueryString("qual")
	strSql = "Select MsgXml from Fila WHERE Seq = " & strqual
	Set RS = objConnection.Execute(strSQL) 
	strXML = RS("MsgXml")
%>
<XML ID = "style" src = "defaultss.xsl" />
<XML ID= "T1">
<%= strXml  %>
</XML>
<SCRIPT FOR="window" EVENT="onload"> 
    xslTarget.innerHTML = T1.transformNode(style.XMLDocument); 
</SCRIPT> 
    <BODY> 
    <DIV id="xslTarget"></DIV> 
  <a href="javascript:window.close()">Fechar</a>
  </BODY>
</HTML>



