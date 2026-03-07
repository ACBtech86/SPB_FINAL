<%@ Language=VBScript %>
<script LANGUAGE="javascript">
function validateSelect()
{
	var msgid;
	msgid = document.MENUMSG.select1.value;
	if (msgid.length = 0)
	{
		return false;
	}
	else
	{
		return true;
	}
}
</script>
<html>
<head>
<meta NAME="GENERATOR" Content="Microsoft Visual Studio 6.0">
</head>
<body>
<table width="750" align="center" cols="0" border="0" cellpadding="0" cellspacing="0">
<p><img src="msgspb.jpg" WIDTH="590" HEIGHT="131">
</p>
</table>
<form NAME="MENUMSG" METHOD="post" ACTION="ValidateMsg.ASP" OnSubmit="return validateSelect()">
<table width="750" align="center" cols="0" border="0" cellpadding="0" cellspacing="0">
<!-- #INCLUDE file="connect.asp" -->
<%
  Dim objConnection ' As Object
  Dim objRS ' As Object
  Dim strSQL ' As String  
  Dim strMsgid ' As String  
  Dim strItem ' As String  
  Set objConnection = CreateObject("adodb.connection")
	  objConnection.Open strDBConnection
      strSQL = "SELECT * FROM MENSAGEM_SPB "  
      Set objRS = objConnection.Execute(strSQL)
%>  
	  <select id="select1" style="WIDTH: 750px; HEIGHT: 200px" size="2" name="select1">&quot;) 
	  <option selected>Selecione a Mensagem</option>&quot;)
<%
      While NOT objRS.EOF
      strMsgid = trim(objRS("MSG_ID"))
      strItem = left(strMsgid,10) & " - " & objRS("MSG_DESCR")
%>  
	  <option value="<%=strMsgid%>"><%=strItem%></option>
<%
        objRS.moveNext
      Wend
%>  
      </select>
<input NAME="btnSubmit" TYPE="submit" VALUE="Selecione">
</table>
</form>
</body>
</html>
