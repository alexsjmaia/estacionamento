package model

type DadosEstacionamento struct {
	Cnpj               string `json:"cnpj"`
	InscricaoMunicipal string `inscricao:"inscricao_municipal"`
	Nome               string `json:"nome"`
	Telefone           string `json:"telefone"`
	WhatsApp           string `json:"whatsapp"`
	Email              string `email:"email"`
	Endereco
}
