<%@ Language=VBScript %>
<%OPTION EXPLICIT%>
<HTML>
  <HEAD>
    <TITLE>Atualiza SPB </TITLE>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<LINK REL="stylesheet" TYPE="text/css" HREF="cidadespb.css" TITLE="formal">
</head>
<body bgcolor="#FFFFFF" text="#000000">
<!-- #include file="menu.inc" -->
  <TABLE border="0">

<%
Dim strField ' As String
Dim strSelect ' As String
Dim strName ' As String
strSelect = Request.Form("processados")
%>
<tr>
<td><%= strSelect %></td>
</tr>
</table>
</body>
</html>
