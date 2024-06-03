package cadastroDeVeiculo

import (
	"estacionamento/dataBase"
	"fmt"
	"log"
	"strings"
)

// Existe uma outra estrutura de veiculo no pacote entrada.go
type veiculo struct {
	placa  string
	modelo string
	cor    string
}

func CadastrarVeiculo(placa string) (modelo, cor string) {
	var carro veiculo

	carro.placa = placa

	fmt.Println("Cadastrando o Veiculo de Placa", placa)
	fmt.Printf("Digite o modelo:")
	fmt.Scanln(&carro.modelo)
	carro.modelo = strings.ToUpper(carro.modelo)
	fmt.Printf("Digite a Cor do Veiculo:")
	fmt.Scanln(&carro.cor)
	carro.cor = strings.ToUpper(carro.cor)
	fmt.Println(carro.placa, carro.modelo, carro.cor)

	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados")
	}
	defer db.Close()

	statement, err := db.Prepare("insert into cadastroDeVeiculos (placa, modelo, cor) values (?, ?, ?)")

	if err != nil {
		log.Fatal("Erro ao conectar no banco de dados", err)
	}

	resultado, err := statement.Exec(placa, carro.modelo, carro.cor)

	if err != nil {
		log.Fatal("Erro ao gravar os dados no banco de dados", err)
	}

	ultimoIdInserido, err := resultado.LastInsertId()
	if err != nil {
		fmt.Println("Erro ao capturar o Ultimo ID inserido", err, ultimoIdInserido)
	}
	fmt.Println("Veiculo cadastrado com Sucesso", ultimoIdInserido, carro.placa, carro.modelo, carro.cor)

	//////////////////////////////////////////////////////////////////////////////////////////
	//idInserido := entradaDeVeiculos.ExecutaEntrada(carro.placa, carro.modelo, carro.cor)

	//if idInserido == 0 {
	//	fmt.Println("Não Foi Possivel dar Entrada no Veiculo")
	//} else {
	//	fmt.Println("Imprimir Comprovante")
	//	impressao.ImprimirEntrada(carro.placa, carro.modelo, carro.cor, idInserido)
	//}
	////////////////////////////////////////////////////////////////////////////////

	return carro.modelo, carro.cor
}
