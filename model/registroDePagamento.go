package model

import "time"

type RegistroPagamento struct {
	ID       int64     `json:"id"`
	DataHora time.Time `json:"data_hora"`
	Placa    string    `json:"placa"`
	Valor    float64   `json:"valor"`
}
