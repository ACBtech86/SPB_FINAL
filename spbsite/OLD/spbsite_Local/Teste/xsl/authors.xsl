<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/TR/WD-xsl">
	<xsl:template match="/">
		<h1>Authors</h1>
		<table cellpadding="3" cellspacing="0">
			<tr>
				<th>SSN</th>
				<th>Last Name</th>
				<th>First Name</th>
				<th>Phone</th>
			</tr>
			<xsl:apply-templates select="//author"/>
		</table>
	</xsl:template>
	<xsl:template match="author">
		<tr>
			<td><xsl:value-of select="au_id" /></td>
			<td><xsl:value-of select="au_lname" /></td>
			<td><xsl:value-of select="au_fname" /></td>
			<td><xsl:value-of select="phone" /></td>
		</tr>
	</xsl:template>
</xsl:stylesheet>

