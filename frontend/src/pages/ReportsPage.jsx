import Header from "../components/Header";


function ReportsPage() {
  return (
    <div className="page">

      <Header
        title="Reports"
        subtitle="Portfolio and borrower intelligence reporting workspace."
      />


      <section className="section-card">

        <div className="empty-state">

          <h2>
            Reporting Workspace
          </h2>

          <p>
            Portfolio deterioration reports,
            intervention summaries and borrower
            review packs will be generated here.
          </p>

          <span>
            Report generation will be added in a later development block.
          </span>

        </div>

      </section>

    </div>
  );
}


export default ReportsPage;