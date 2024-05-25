package model

type Veiculo struct {
	Placa  string       `json:"placa"`
	Modelo string       `json:"modelo"`
	Cor    string       `json:"cor"`
	Tipo   *TipoVeiculo `json:"tipo_veiculo"`
}
