<%@ Language=VBScript %>
<%OPTION EXPLICIT%>
<HTML>
  <HEAD>
    <TITLE>Form SPB Mensagem Page</TITLE>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<LINK REL="stylesheet" TYPE="text/css" HREF="cidadespb.css" TITLE="formal">
</head>
<body bgcolor="#FFFFFF" text="#000000">
<!-- #include file="menu.inc" -->
  <TABLE border="0">
<!-- #INCLUDE file="connect.asp" -->
<%
Dim strField ' As String
Dim strSelect ' As String
Dim strName ' As String

strSelect = Request.QueryString("selectl")
strName = Request.Form("formName")
'Response.write("<BR><B>Debug strSelect=" & strSelect & "</B>")
'Response.write("<BR><B>Debug name=" & strName & "</B>")
strPath      = ""
strFormName  = ""
strFormStyle = ""
strFormError = "error"

if strSelect <> "" then
strFormName  = strSelect
strFormStyle = strSelect
elseif strName <> "" then
strFormName  = strName
strFormStyle = strName
end if

If processForm(strFormName,Request) = "validated" Then 
'   Response.Write("Form validado!<BR/>Aqui os campos e seus conteudos:")
'   For Each strField In Request.Form
'       Response.Write("<BR><B>" & strField & "</B> = " & Request.Form(strField))
'   Next
	If MsgFormXml(strFormName,Request) = "validated" Then 
'		Response.Write("<BR/> Mensagem Gerada!")
	End If
End If


%>
</td></TR>
</TABLE>
  </BODY>
</HTML>


<%
'===================================================================='
'        S U B R O U T I N E S  A N D  F U N C T I O N S             ' 
'===================================================================='
%>
<!-- #INCLUDE file="processSPBForm.asp" -->
<!-- #INCLUDE file="msgformxml.asp" -->
