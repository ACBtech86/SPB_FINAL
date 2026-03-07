<?xml version="1.0" encoding="UTF-8"?>
<!-- edited with XML Spy v3.5 NT (http://www.xmlspy.com) by Antonio Correa Bosco (Banco Cidade S.A.) -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/TR/WD-xsl">
	<xsl:template match="/">
		<SCRIPT LANGUAGE="javascript" src="funcoes.js"></SCRIPT>
		<!-- output any error messages -->
		<xsl:apply-templates select="FORM/FORM-ERRORS"/>
		<!-- build the form -->
		<table>
		<FORM name="form1"  method ="post" >
			<xsl:attribute name="action">ValidateMsgSPB.asp
			?form=<xsl:value-of select="FORM/@name"/>
			&amp;TKS=<xsl:value-of select="FORM/FIELDSET/@TKS"/>
			</xsl:attribute>
			<!-- hidden fields for name and status : always include -->
			<INPUT type="hidden" name="formName">
				<xsl:attribute name="value"><xsl:value-of select="FORM/@name"/></xsl:attribute>
			</INPUT>
			<INPUT type="hidden" name="formStatus">
				<xsl:attribute name="value"><xsl:value-of select="FORM/@status"/></xsl:attribute>
			</INPUT>
			<INPUT type="hidden" name="formIdentdDestinatario">
				<xsl:attribute name="value"><xsl:value-of select="FORM/FIELDSET/@destino"/></xsl:attribute>
			</INPUT>
			<INPUT type="hidden" name="formCodGrade">
				<xsl:attribute name="value"><xsl:value-of select="FORM/FIELDSET/@codgrade"/></xsl:attribute>
			</INPUT>
			<TABLE width="100%" align="center" cols="0" border="1" cellpadding="0" cellspacing="0">
				<TR>
					<TD align="center" bgColor="midnightblue"><FONT face="verdana" size="2" color="white"><strong><xsl:value-of select="FORM/@name"/> - <xsl:value-of select="FORM/@title"/></strong></FONT>
					</TD>
<!--
					<TD width="10">	
						<a >
							<xsl:attribute name="href">Lista_Mensagens.asp?Cod_Grade=
								<xsl:value-of select="FORM/FIELDSET/@codgrade"/>
								&ISPB_Destino=
								<xsl:value-of select="FORM/FIELDSET/@destino"/>
							</xsl:attribute>
		   					<img src="../imagens/seta_azul.gif" border="0">
								<font face="Verdana" color="white" size=2>
									<b>Voltar</b>
								</font>
							</img>	
						</a>
					</TD >
-->
				</TR>
			</TABLE>
			<div id="formspb" style="overflow-y:scroll; width:100%; height:280px; z-index:0; left: auto; top: 75px">
			<TABLE width="100%" align="center" cols="2" border="0" cellpadding="1" cellspacing="1">
			
			<xsl:apply-templates select="//FIELDSET">
			</xsl:apply-templates>
			<xsl:apply-templates select="//FIELDSET/FIELD | //FIELDSET/FIELDREPET | //FIELDSET/FIELDGRUPO ">
			</xsl:apply-templates>
			
			</TABLE>
			</div>
			<TABLE width="100%" align="center" cols="0" border="1" cellpadding="0" cellspacing="0">
				<TR>
					<TD  align="center" bgColor="midnightblue">
						<A>
							<xsl:attribute name="href">JavaScript:Repet()</xsl:attribute> 													<IMG src="../Imagens/refresh-ico.gif" align="middle" border="0">														<font face="verdana" size="2" color="#ffffff"><strong>Gera Repetição/Grupo</strong></font>
							</IMG>	
						</A> 	
 					</TD>
					<TD align="center" bgColor="midnightblue">
							<A href="JavaScript:Envia()">
								<IMG src="../Imagens/inclui-ico.jPG" align="middle" border="0">															<font face="verdana" size="2" color="#ffffff"><strong>Gera Mensagem</strong></font>
								</IMG>	
							</A> 	
					</TD>
				</TR>
			</TABLE>
			</FORM>
			</table>
	</xsl:template>
	<!-- standard templates for form fields and errors -->
	<xsl:template match="FIELDSET">		
		<xsl:if test="@spbtag[.='GENReqECO' or .='GENReqUltMsg' or .='GENAvisComunicado']">
			<TR>
					<TD  colspan="2" align="center" bgColor="midnightblue">
						<font face="verdana" size="2" color="#ffffff"><strong>BCMSG</strong></font>
					</TD>
			</TR>
			<TR>
				<TD align="left" bgColor="f1C0B0">
					<FONT face="verdana" size="1"><strong>
				       ISPB do Destinatário:
					</strong></FONT>
				</TD>
				<TD align="left" bgColor="f1C0B0">
					<INPUT type="text" size="8" maxlength="8" >
						<xsl:attribute name="readonly"/>
						<xsl:attribute name="name">IdentdDestinatario</xsl:attribute>
						<xsl:attribute name="value"><xsl:value-of select="@destino"/></xsl:attribute>
					</INPUT>
<!--					
					<input type="radio">
					<xsl:attribute name="onClick">javascript:fG_AbrePaleta('IdentdDestinatario','ISPBDESTINO')</xsl:attribute>
					</input><FONT face="Arial" color="green" size="1">help</FONT>
-->
				</TD>
			</TR>
			<TR>
					<TD  colspan="2" align="center" bgColor="midnightblue">
						<font face="verdana" size="2" color="#ffffff"><strong>SISMSG</strong></font>
					</TD>
			</TR>
		</xsl:if>
	</xsl:template>
	
	<xsl:template match="FIELDREPET">		
			<TR>
				<TD align="left" bgColor="ffffd0">
					<FONT face="verdana" size="1"><strong>
				       <xsl:value-of select="@label"/>:
					</strong></FONT>
				</TD>
				<TD align="left" bgColor="ffffd0">
					<INPUT type="text" size="2" maxlength="2" >
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
						<xsl:attribute name="value"><xsl:value-of select="@occurs"/></xsl:attribute>
					</INPUT>
				</TD>
			</TR>
     <xsl:apply-templates select="FIELDGRUPO | FIELD" />
			<TR>
				<TD colspan="2" align="left" bgColor="ffffd0">
					<FONT face="verdana" size="1"><strong>
				       Fim <xsl:value-of select="@label"/>
					</strong></FONT>
				</TD>
			</TR>
	</xsl:template>
	<xsl:template match="FIELDGRUPO">		
			<TR>
				<xsl:if test="@req[.='yes']">
					<TD colspan="2"  align="left" bgColor="9fc0e0">
						<FONT face="verdana" size="1"><strong>
					       <xsl:value-of select="@label"/>:
						</strong></FONT>
					</TD>
				</xsl:if>
				<xsl:if test="@req[.='no']">
					<TD align="left" bgColor="9fc0e0">
						<FONT face="verdana" size="1"><strong>
					       <xsl:value-of select="@label"/>:
						</strong></FONT>
					</TD>
					<TD align="left" bgColor="9fc0e0">
						<FONT face="verdana" size="1"><strong>Expande grupo</strong></FONT>
						<INPUT type="checkbox" >
							<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
							<xsl:attribute name="value"><xsl:value-of select="@checked"/></xsl:attribute>
							<xsl:attribute name="onClick">javascript:Grupo_Checked('<xsl:value-of select="@name"/>')</xsl:attribute>
							<xsl:if test="@checked[.='S']">
								<xsl:attribute name="checked"/>
							</xsl:if>
						</INPUT>
					</TD>
				</xsl:if>
			</TR>
    			<xsl:apply-templates select="FIELDREPET | FIELD | FIELDGRUPO" />
	</xsl:template>
	
	
	<xsl:template match="FIELD">
		<TR>
			<TD width="50%" valign="middle" align="right" bgColor="lightsteelblue"><FONT face="verdana" size="1"><strong><xsl:value-of select="@label"/>:</strong></FONT></TD>
			<TD width="50%" valign="middle" align="left" bgColor="f1f1f1">
		<xsl:choose>
			<xsl:when test="@type[.='select']">
				<SELECT>
					<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					<xsl:for-each select="OPTION">
						<OPTION>
							<xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
							<xsl:if test="@selected[.='yes']">
								<xsl:attribute name="selected">yes</xsl:attribute>
							</xsl:if>
							<xsl:value-of select="text()"/>
						</OPTION>
					</xsl:for-each>
				</SELECT>
			</xsl:when>
			<xsl:when test="@type[.='text' or .='date' or .='time' or .='datetime' or .='ccard' or .='email' or .='number']">
				<INPUT type="text">
					<xsl:if test="@name[.!='']">
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@size[.!='']">
						<xsl:attribute name="maxlength"><xsl:value-of select="@size"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@value[.!='']">
						<xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@readonly[.='yes']">
						<xsl:attribute name="readonly"/>
					</xsl:if>
					<xsl:if test="@checked[.='yes']">
						<xsl:attribute name="checked"/>
					</xsl:if>
					<xsl:attribute name="size">
					<xsl:choose>
					<xsl:when test="@size[.&gt;50]">50</xsl:when>
					<xsl:when test="@size[.&gt;0]"><xsl:value-of select="@size"/></xsl:when>
					<xsl:otherwise/></xsl:choose></xsl:attribute>
				</INPUT>
				<!-- teste para ver se o campo tem help de contexto -->
				<xsl:if test="@spbtag[.='CodMsg']">
					<a>
						<xsl:attribute name="onclick">Open_help('<xsl:value-of select="@value"/>')</xsl:attribute>
						<img src="../imagens/help.gif" align="top" border="0"/>
						<FONT face="Arial" color="green" size="1">help</FONT>
					</a>
				</xsl:if>
				<xsl:if test="@help[.!='']">
					<a>
						<xsl:attribute name="onClick">javascript:fG_AbrePaleta('<xsl:value-of select="@name"/>','<xsl:value-of select="@help"/>')</xsl:attribute>
						<img src="../imagens/help.gif" align="top" border="0"/>
						<FONT face="Arial" color="green" size="1">help</FONT>
					</a>
<!--
					<input type="radio">
					<xsl:attribute name="onClick">javascript:fG_AbrePaleta('<xsl:value-of select="@name"/>','<xsl:value-of select="@help"/>')</xsl:attribute>
					</input><FONT face="Arial" color="green" size="1">help</FONT>
-->
				</xsl:if>
				<!-- teste para ver se o campo tem gerar  -->
				<xsl:if test="@gerar[.!='']">
					<a>
					<xsl:attribute name="onClick">javascript:fG_AbreAsp('<xsl:value-of select="@name"/>','<xsl:value-of select="@gerar"/>')</xsl:attribute>
						<img src="../imagens/help.gif" align="top" border="0"/>
						<FONT face="Arial" color="green" size="1">gerar</FONT>
					</a>
<!--	
					<input type="radio">
					<xsl:attribute name="onClick">javascript:fG_AbreAsp('<xsl:value-of select="@name"/>','<xsl:value-of select="@gerar"/>')</xsl:attribute>
					</input><FONT face="Arial" color="green" size="1">gerar</FONT>
-->			
				</xsl:if>
				<xsl:if test="@error[.='yes']">
					<FONT face="verdana" size="2" color="red">*</FONT>
				</xsl:if>
			</xsl:when>
			<xsl:when test="@type[.='textarea']">
				<TEXTAREA>
					<xsl:if test="@name[.!='']">
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					</xsl:if>
					<xsl:attribute name="cols"><xsl:choose><xsl:when test="@cols[.!='']"><xsl:value-of select="@cols"/></xsl:when><xsl:otherwise>50</xsl:otherwise></xsl:choose></xsl:attribute>
					<xsl:if test="@readonly[.='yes']">
						<xsl:attribute name="readonly"/>
					</xsl:if>
					<xsl:attribute name="rows"><xsl:choose><xsl:when test="@rows[.!='']"><xsl:value-of select="@rows"/></xsl:when><xsl:otherwise>3</xsl:otherwise></xsl:choose></xsl:attribute>
					<xsl:choose>
						<xsl:when test="@value[.!='']">
							<xsl:value-of select="@value"/>
						</xsl:when>
						<xsl:otherwise>Enter text</xsl:otherwise>
					</xsl:choose>
				</TEXTAREA>
			</xsl:when>
			<xsl:when test="@type[.='radio']">
				<INPUT type="radio">
					<xsl:if test="@name[.!='']">
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@value[.!='']">
						<xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@readonly[.='yes']">
						<xsl:attribute name="readonly"/>
					</xsl:if>
					<xsl:if test="@checked[.='yes']">
						<xsl:attribute name="checked"/>
					</xsl:if>
				</INPUT>
			</xsl:when>
			<xsl:when test="@type[.='checkbox']">
				<INPUT type="checkbox">
					<xsl:if test="@name[.!='']">
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@value[.!='']">
						<xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@readonly[.='yes']">
						<xsl:attribute name="readonly"/>
					</xsl:if>
					<xsl:if test="@checked[.='yes']">
						<xsl:attribute name="checked"/>
					</xsl:if>
				</INPUT>
			</xsl:when>
			<xsl:otherwise>
				<INPUT>
					<xsl:attribute name="type"><xsl:value-of select="@type"/></xsl:attribute>
					<xsl:if test="@name[.!='']">
						<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@size[.!='']">
						<xsl:attribute name="maxlength"><xsl:value-of select="@size"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@value[.!='']">
						<xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
					</xsl:if>
					<xsl:if test="@readonly[.='yes']">
						<xsl:attribute name="readonly"/>
					</xsl:if>
					<xsl:if test="@checked[.='yes']">
						<xsl:attribute name="checked"/>
					</xsl:if>
					<xsl:attribute name="size"><xsl:choose><xsl:when test="@size[.&gt;50]">50</xsl:when><xsl:when test="@size[.&gt;0]"><xsl:value-of select="@size"/></xsl:when><xsl:otherwise/></xsl:choose></xsl:attribute>
				</INPUT>
			</xsl:otherwise>
		</xsl:choose>
		</TD>				</TR>
	</xsl:template>
	<xsl:template match="FORM-ERRORS">
			<TABLE width="100%" align="center" cols="0" border="1" cellpadding="0" cellspacing="0">
				<TR>
					<TD  colspan="2" align="center" bgColor="midnightblue">
						<FONT color="white">
							<strong>
								<B>Form com erros. Corrigir os Seguintes Campos:</B>
							</strong>
						</FONT>
					</TD>
				</TR>
			</TABLE>
			<div id="formerro" style="overflow-y:scroll; width:100%; height:100px; z-index:0; left: auto; top: 75px">
			<TABLE width="100%" align="center" cols="0" border="0" cellpadding="0" cellspacing="0">
				<xsl:for-each select="ERROR">
					<TR>
						<TD  width="50%"  align="right" bgColor="lightsteelblue">
							<FONT color="black">
								<xsl:value-of select="@name"/>:
							</FONT>
						</TD>
						<TD  align="left" bgColor="f1f1f1">
							<FONT color="black">
								<xsl:value-of select="@message"/>
							</FONT>
						</TD>
					</TR>
				</xsl:for-each>
			</TABLE>
			</div>
			<TABLE width="100%" align="center" cols="0" border="1" cellpadding="0" cellspacing="0">
				<TR>
					<TD  colspan="2" align="center" bgColor="midnightblue">
						<FONT color="white">
							<strong>
								<B>Fim Erros</B>
							</strong>
						</FONT>
					</TD>
				</TR>
			</TABLE>
	</xsl:template>
</xsl:stylesheet>

