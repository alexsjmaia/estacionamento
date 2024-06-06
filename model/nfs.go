package model

import "time"

type nfs struct {
	Emitente           DadosDaEmpresa
	Cliente            Mensalista
	NumeroNota         uint64    `json:"numero_nota"`
	NumeroRps          uint64    `json:"numero_rps"`
	Data               time.Time `json:"data"`
	DescricaoDoServiso string    `json:"descricao_servico"`
	Valor              float64   `json:"valor"`
}
