package model

import "time"

type Mensalista struct {
	Cpf          string     `json:"cpf"`
	Nome         string     `json:"nome"`
	DataCadastro time.Time  `json:"data_cadastro"`
	Bloqueado    bool       `json:"bloqueado"`
	Veiculos     *[]Veiculo `json:"veiculos"`
}
