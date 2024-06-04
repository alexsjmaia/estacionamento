package model

type Operador struct {
	ID     int64  `json:"id"`
	Codigo int64  `json:"codigo"`
	Nome   string `json:"nome"`
	Senha  string `json:"senha"`
	Tipo   string `json:"tipo"`
}
