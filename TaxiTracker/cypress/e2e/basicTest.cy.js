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
    cy.contains("a", "Назад к списку").click();
    cy.contains("button", "Выйти").click();
      });

  });
});