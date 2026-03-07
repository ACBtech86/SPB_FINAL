<%@ Language=VBScript %>
<%OPTION EXPLICIT%>
<HTML>
  <HEAD>
    <TITLE>Form SPB Mensagem Page</TITLE>
  </HEAD>
<BODY>
  <P align="center"><FONT face="verdana" size="3" color="navy">Mensagem SPB</FONT></P>
  <TABLE border="0" id=TABLE1>
<!-- #INCLUDE file="connect.asp" -->
<%
Dim strField ' As String
Dim strSelect ' As String
Dim strName ' As String

strSelect = Request.Form("select1")
strName = Request.Form("formName")

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
   Response.Write("Form validado!<BR/>Aqui os campos e seus conteudos:")
   For Each strField In Request.Form
       Response.Write("<BR><B>" & strField & "</B> = " & Request.Form(strField))
   Next
	If MsgFormXml(strFormName,Request) = "validated" Then 
		Response.Write("<BR/> Mensagem Gerada!")
	else
		Response.Write("<BR/> Mensagem Erro!")
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
