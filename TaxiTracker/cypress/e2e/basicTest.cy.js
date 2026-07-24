describe("Manager workflow", () => {
  it("Login and open enterprise", () => {
    cy.visit("http://localhost:8000/login");

    cy.get('input[name="username"]').type("manager_1");
    cy.get('input[name="password"]').type("051587Asd)");

    cy.get('button[type="submit"], input[type="submit"]').click();

    cy.url().should("not.include", "/login");

    cy.contains("td", "ООО Лимон")
      .closest("tr")
      .click();

    cy.url().should("include", "/vehicles_dashboard/");


    cy.contains("a", "Добавить автомобиль").click();

    cy.get("#id_prod_date").type("2026-01-01");

    cy.get("#id_enterprise").select(3);

    cy.get("#id_odometer").type("10000");

    cy.get("#id_price").type("2500000");

    cy.get("#id_color").type("Черный");

    cy.get("#id_plate_number").type("А123АА77");

    // Бренд (value = 1)
    cy.get("#id_brand").select("1");

    // Водитель (если на странице есть select с id="id_driver")
    cy.get("#id_driver").select("");
    cy.contains("button", "Создать автомобиль").click();

    cy.get("tbody tr")
      .first()
      .click();

    cy.get("#editBtn").click();

    cy.get("#id_driver")
      .should("be.visible")
      .and("not.be.disabled");

    cy.get("#id_driver")
      .find("option")
      .eq(1)
      .then(($option) => {
        cy.get("#id_driver")
          .select($option.val());

    cy.get("#saveBtn").click();
    cy.get('a[href*="format=csv"]').click();
    cy.get('a[href*="format=json"]').click();

    cy.get("#editBtn").click();

    cy.get("#id_driver")
      .should("be.visible")
      .and("not.be.disabled");

    cy.get("#id_driver")
      .find("option")
      .eq(0)
      .then(($option) => {
        cy.get("#id_driver")
          .select($option.val());

    cy.get("#saveBtn").click();

    cy.contains("a", "Назад к списку").click();
    cy.get("tbody tr")
      .first()
      .find('input.vehicle-checkbox')
      .check();
    cy.contains("button", "Удалить выбранные").click();


    cy.contains("button", "Выйти").click();
      });
    });
  });
});