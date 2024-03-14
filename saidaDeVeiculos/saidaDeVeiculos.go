// ELISA
package saidadeveiculos

import (
	"estacionamento/dataBase"
	"fmt"
	"log"
	"time"
)

func SaidaDeveiculos() {

	var idProcurado int
	fmt.Printf("Digite o número da entrada:")
	fmt.Scanln(&idProcurado)

	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados para buscar veiculo cadastrado")
	}
	defer db.Close()

	var (
		id                                                  int
		placa, modelo, cor, veiculoNoPatio, dataHoraEntrada string
	)

	linha, err := db.Query("SELECT id, placa, modelo, cor, dataHoraEntrada, veiculoNoPatio FROM estacionamento.entradaDeVeiculos where id = ?", idProcurado)
	if err != nil {
		log.Fatal("Erro ao criar o statement", err)
	}
	defer linha.Close()

	if linha.Next() {
		if err := linha.Scan(&id, &placa, &modelo, &cor, &dataHoraEntrada, &veiculoNoPatio); err != nil {
			log.Fatal("Erro ao buscar a entrada do veiculo no banco", err)
		}

		if idProcurado == id {
			if veiculoNoPatio == "N" {
				fmt.Println("O Veiculo Já Saiu do Pátio")
			} else {

				dataHoraDeSaida := time.Now()

				dataHoraEntradaTime, err := time.Parse("2006-01-02 15:04:05", dataHoraEntrada)
				if err != nil {
					panic(err.Error())
				}

				tempoDePermanencia := dataHoraDeSaida.Sub(dataHoraEntradaTime)

				fmt.Println("Data e hora de Entrada", dataHoraEntrada)
				fmt.Println("Data e hora de saida : ", dataHoraDeSaida)
				fmt.Println("Tempo de permanencia : ", tempoDePermanencia)
			}
		}
	}
}
