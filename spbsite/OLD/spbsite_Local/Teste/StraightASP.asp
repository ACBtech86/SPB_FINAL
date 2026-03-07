<%@ Language=VBScript %>

<% Function GetRecordset()
	Dim cnn
	
	Set cnn = CreateObject("ADODB.Connection")
	cnn.Open "driver={SQL Server};server=srv-gersut;uid=soft10;pwd=look"
	cnn.DefaultDatabase = "pubs"
	Set GetRecordset = cnn.Execute("select * from authors")
End Function %>   

<html>
<head>
<title>Straight ASP Approach</title>
<link rel="stylesheet" type="text/css" href="../default.css">
</head>
<body>

<h1>Authors</h1>

<table cellpadding="3" cellspacing="0">
	<tr>
		<th>SSN</th>
		<th>Last Name</th>
		<th>First Name</th>
		<th>Phone</th>
	</tr>
	<%  Dim rs
		Set rs = GetRecordset()
		While Not rs.EOF %>
			<tr>
				<td><%=rs("au_id")%></td>
				<td><%=rs("au_lname")%></td>
				<td><%=rs("au_fname")%></td>
				<td><%=rs("phone")%></td>
			</tr>
	<%		rs.MoveNext 
		Wend
		rs.Close
		Set rs = Nothing
	%>
</table>
</body>
</html>