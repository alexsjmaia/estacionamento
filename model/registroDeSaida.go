package model

import "time"

type RegistroSaida struct {
	ID                  int64            `json:"id"`
	Placa               string           `json:"placa"`
	DataSaida           time.Time        `json:"data_saida"`
	TempoDePermanencia  time.Time        `json:"tempo_permanencia"`
	ValorCobrado        float64          `json:"valor_cobrado"`
	RegistroDeEntradaID *RegistroEntrada `json:"registro_de_entrada"`
}
