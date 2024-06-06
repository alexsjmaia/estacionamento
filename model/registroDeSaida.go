package model

import "time"

type RegistroSaida struct {
	ID                  int64            `json:"id"`
	Placa               string           `json:"placa"`
	DataSaida           time.Time        `json:"data_saida"`
	TempoDePermanencia  time.Time        `json:"tempo_permanencia"`
	ValorCobrado        float64          `json:"valor_cobrado"`
	TipoDePagamento     string           `json:"tipo_pagamento"`
	RegistroDeEntradaID *RegistroEntrada `json:"registro_de_entrada"`
	Mensalista          *Mensalista      // Para emitir a NF-s vamos precisar dos dados do mensalista, caso ele peça nota. também ele pode ser Bloqueado por falta de pagamento
}
