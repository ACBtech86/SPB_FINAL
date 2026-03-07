<%@ Language=VBScript %>
<!-- #INCLUDE FILE="inc/xmlutil.asp" -->

<% Function GetRecordset()
	Dim cnn
	
	Set cnn = CreateObject("ADODB.Connection")
	cnn.Open "driver={SQL Server};server=srv-gersut;uid=soft10;pwd=look"
	cnn.DefaultDatabase = "pubs"
	parm = Request.Form("txtUserid")
	Set GetRecordset = cnn.Execute("select * from authors where au_fname like '" & parm & "%'")
End Function %>   

<html>
<head>
<title>Straight XML Approach</title>
<link rel="stylesheet" type="text/css" href="../default.css">
</head>
<body>
	<% = TransformXML( RecordsetToXMLDoc(GetRecordset(), "author"), "xsl/authors.xsl" ) %>
</body>
</html>