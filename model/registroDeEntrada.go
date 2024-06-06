package model

import "time"

type RegistroEntrada struct {
	ID          int64       `json:"id"`
	Placa       string      `json:"placa"`
	DataEntrada time.Time   `json:"data_entrada"`
	EstaNoPatio bool        `json:"esta_no_patio"`
	Mensalista  *Mensalista // Referenciado pois o cliente pode estar bloqueado, neste caso ele não poderá mais estacionar até quitar os débitos
	Observacao  string      `json:"observacao"`
}
