package model

import "time"

type RegistroEntrada struct {
	ID          int64     `json:"id"`
	Placa       string    `json:"placa"`
	DataEntrada time.Time `json:"data_entrada"`
	EstaNoPatio bool      `json:"esta_no_patio"`
	Observacao  string    `json:"observacao"`
}
