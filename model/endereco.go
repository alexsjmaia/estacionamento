package model

type Endereco struct {
	Cep         string `json:"cep"`
	Logradouro  string `json:"logradouro"`
	Estado      string `json:"estado"`
	Cidade      string `json:"cidade"`
	Uf          string `json:"uf"`
	Bairro      string `json:"bairro"`
	Numero      uint64 `json:"logradouro"`
	Complemento string `json:"complemento"`
}
