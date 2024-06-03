package entradaDeVeiculos

import (
	"estacionamento/cadastroDeVeiculo"
	"estacionamento/dataBase"
	impressao "estacionamento/imprimirComprovante"
	"fmt"
	"log"
	"regexp"
	"strings"
)

func validarPlaca(placa string) bool {
	// Expressão regular para validar placa de carro no padrão brasileiro
	regexpPlaca := regexp.MustCompile(`^[A-Z]{3}[0-9]{4}$`)
	return regexpPlaca.MatchString(placa)
}

func Entrada() {
	var pla string
	fmt.Printf("Digite a placa:")
	strings.ToUpper(pla)
	fmt.Scanln(&pla)

	// Validando a Placa
	if !validarPlaca(pla) {
		fmt.Println("Placa Inválida!")
		Entrada() // Não sei se isto está certo
	}

	// Verificar se o Veiculo possui cadastro
	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados para buscar veiculo cadastrado")
	}
	defer db.Close()

	linha, err := db.Query("SELECT * FROM estacionamento.cadastroDeVeiculos where placa = ?", pla)
	if err != nil {
		log.Fatal("Erro ao criar o statement", err)
	}
	defer linha.Close()

	var id int
	var placa string
	var modelo string
	var cor string

	if linha.Next() {
		if err := linha.Scan(&id, &placa, &modelo, &cor); err != nil {
			log.Fatal("Erro ao buscar veiculo no banco")
		}
	}
	if pla == placa {
		fmt.Println("Veiculo já Cadastrado", id, placa, modelo, cor)

		idInserido := ExecutaEntrada(placa, modelo, cor)
		if idInserido == 0 {
			fmt.Println("Não Foi Possivel dar Entrada no Veiculo")
		} else {
			fmt.Println("Imprimir Comprovante")

			impressao.ImprimirEntrada(placa, modelo, cor, int64(idInserido))
		}

	} else {
		modelo, cor := cadastroDeVeiculo.CadastrarVeiculo(pla)
		ExecutaEntrada(pla, modelo, cor)
	}

}
