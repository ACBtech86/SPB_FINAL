<%@ Language=VBScript %>
<!-- #INCLUDE FILE="inc/xmlutil.asp" -->

<% Function GetRecordset()
	Dim cnn
	
	Set cnn = CreateObject("ADODB.Connection")
	cnn.Open "driver={SQL Server};server=srv-gersut;uid=soft10;pwd=look"
	cnn.DefaultDatabase = "bcspbstr"
	Set GetRecordset = cnn.Execute("select * from bcidade_to_bacen_app")
End Function %>   

<html>
<head>
<title>Straight XML Approach</title>
<link rel="stylesheet" type="text/css" href="../default.css">
</head>
<body>
	<h1>Default IE5 View</h1>
	<% = TransformXML( RecordsetToXMLDoc(GetRecordset(), "BCIDADE_TO_BACEN_APP"), "bwsebacen2cidade.xsl" ) %>
</body>
</html>